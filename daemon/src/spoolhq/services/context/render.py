"""Rendering prompts from Jinja2 templates in a sandbox.

Untrusted text (the ticket, the spec, the repository's notes, gate output, review notes,
user notes) is only ever passed to a template as a variable, never as template source:
templates are loaded by name from the package or from the workspace's ``prompts/``
folder. Each untrusted value sits in its own tag block (``<ticket>…</ticket>``), and any
copy of that block's closing tag inside the value is escaped here, before rendering,
so an override cannot forget it.
"""

import re
from collections.abc import Callable, Mapping
from importlib import resources
from pathlib import Path
from typing import Any

from jinja2 import (
    BaseLoader,
    Environment,
    StrictUndefined,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
    UndefinedError,
)
from jinja2.exceptions import SecurityError
from jinja2.sandbox import SandboxedEnvironment

from spoolhq.core.agent_policy import READ_ONLY_GIT
from spoolhq.services.context.budget import (
    CLAUDE_MD_CAP,
    DECISIONS_CAP,
    MIN_CONTEXT_ROOM,
    PROGRESS_CAP,
    Trimmed,
    cap_excerpt,
    keep_head,
    keep_newest_entries,
    newest_entries,
    newest_lines,
    select_spec,
    words,
)
from spoolhq.services.context.errors import ContextBudgetError, PromptTemplateError
from spoolhq.services.context.model import ContextInputs, PreviousAttempt, RenderedPrompt

PACKAGE = "spoolhq.services.context"
TEMPLATE_DIR = "prompts"
IMPLEMENTER_TEMPLATE = "implementer.md.j2"
DEFAULT_LABEL = "default"

_TEMPLATE_NAME_RE = re.compile(r"[a-z][a-z0-9_-]*\.md\.j2")
_FIT_ATTEMPTS = 3
_UNDEFINED_NAME_RE = re.compile(r"'(?P<name>[^']+)' is undefined")


# Values ----------------------------------------------------------------------------


def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def escape_closing_tag(text: str, tag: str) -> str:
    """Escape every ``</tag>`` (any case, with or without spaces) as ``<\\/tag>``."""
    pattern = re.compile(rf"<\s*/\s*({re.escape(tag)})\s*>", re.IGNORECASE)
    return pattern.sub(lambda match: f"<\\/{match.group(1)}>", text)


def _clean(text: str, tag: str) -> str:
    return escape_closing_tag(normalize_newlines(text), tag)


def fenced(text: str) -> str:
    """``text`` in a code fence longer than any backtick run inside it.

    Leading and trailing blank lines are left out; the text itself is unchanged.
    """
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    body = text.strip("\n")
    return f"{fence}\n{body}\n{fence}"


def code(text: str) -> str:
    """``text`` as an inline code span that its own backticks cannot end."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    ticks = "`" * (longest + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{ticks}{pad}{text}{pad}{ticks}"


# Templates -------------------------------------------------------------------------


class _PromptLoader(BaseLoader):
    """Loads ``<override_dir>/<name>`` if it exists, else the packaged default."""

    def __init__(self, override_dir: Path | None) -> None:
        self.override_dir = override_dir
        self.label = DEFAULT_LABEL

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str, Callable[[], bool]]:
        if not _TEMPLATE_NAME_RE.fullmatch(template):
            raise TemplateNotFound(template)
        if self.override_dir is not None:
            path = self.override_dir / template
            if path.is_file():
                self.label = f"{self.override_dir.name}/{template}"
                source = normalize_newlines(path.read_text(encoding="utf-8"))
                return source, self.label, lambda: False
        packaged = resources.files(PACKAGE).joinpath(TEMPLATE_DIR, template)
        if not packaged.is_file():
            raise TemplateNotFound(template)
        source = normalize_newlines(packaged.read_text(encoding="utf-8"))
        return source, f"{template} (default)", lambda: True


class PromptTemplate:
    """A loaded template; ``render`` turns every template failure into a one-liner."""

    def __init__(self, name: str, *, override_dir: Path | None = None) -> None:
        loader = _PromptLoader(override_dir)
        env = SandboxedEnvironment(
            loader=loader,
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["fenced"] = fenced
        env.filters["code"] = code
        try:
            self._template: Template = env.get_template(name)
        except TemplateSyntaxError as exc:
            where = exc.filename or name
            raise PromptTemplateError(
                f"{where}: syntax error at line {exc.lineno}: {exc.message}"
            ) from exc
        except TemplateNotFound as exc:
            raise PromptTemplateError(f"no prompt template named {name!r}") from exc
        self.label = loader.label
        self.filename = self._template.filename or name

    def render(self, variables: Mapping[str, Any]) -> str:
        """Render with ``\\n`` line endings only, ending with exactly one newline."""
        where = self.filename
        try:
            text = self._template.render(variables)
        except SecurityError as exc:
            raise PromptTemplateError(f"{where}: not allowed in a SpoolHQ template: {exc}") from exc
        except UndefinedError as exc:
            match = _UNDEFINED_NAME_RE.fullmatch(str(exc))
            what = f"undefined variable '{match['name']}'" if match else f"undefined value: {exc}"
            line = _template_line(exc, where)
            suffix = f" (line {line})" if line is not None else ""
            raise PromptTemplateError(f"{where}: {what}{suffix}") from exc
        except Exception as exc:  # anything else an override can trigger, e.g. 1 + 'a'
            raise PromptTemplateError(f"{where}: error while rendering: {exc}") from exc
        return normalize_newlines(text).rstrip("\n") + "\n"


def _template_line(exc: BaseException, filename: str) -> int | None:
    """The template line of the innermost frame Jinja attributed to ``filename``."""
    line = None
    tb = exc.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == filename:
            line = tb.tb_lineno
        tb = tb.tb_next
    return line


def render_template(
    name: str, variables: Mapping[str, Any], *, override_dir: Path | None = None
) -> tuple[str, str]:
    """Render the template ``name`` (an override in ``override_dir`` wins).

    Returns the text and ``"default"`` or the override's path relative to the workspace.
    Callers must escape untrusted values first (see ``escape_closing_tag``).
    """
    template = PromptTemplate(name, override_dir=override_dir)
    return template.render(variables), template.label


# The implementer prompt ------------------------------------------------------------


def _ticket_vars(inputs: ContextInputs) -> dict[str, Any]:
    ticket = inputs.ticket
    return {
        "id": _clean(ticket.id, "ticket"),
        "title": _clean(ticket.title, "ticket"),
        "body": _clean(ticket.body, "ticket"),
        "review_required": ticket.review_required,
        "depends_on": [
            {
                "id": _clean(dep.id, "ticket"),
                "title": _clean(dep.title, "ticket"),
                "status": _clean(dep.status, "ticket"),
            }
            for dep in ticket.depends_on
        ],
    }


def _previous_vars(previous: PreviousAttempt | None) -> dict[str, Any] | None:
    if previous is None:
        return None
    tag = "previous_attempt"
    return {
        "kind": previous.kind,
        "number": previous.number,
        "failing_tests": [_clean(name, tag) for name in previous.failing_tests],
        "gate_failures": [
            {
                "command": _clean(failure.command, tag),
                "exit_code": failure.exit_code,
                "timed_out": failure.timed_out,
                "output": _clean(cap_excerpt(normalize_newlines(failure.output_excerpt)), tag),
            }
            for failure in previous.gate_failures
        ],
        "review_notes": [
            {"item": _clean(note.item, tag), "met": note.met, "reason": _clean(note.reason, tag)}
            for note in previous.review_notes
        ],
        "conflict_files": [_clean(path, tag) for path in previous.conflict_files],
        "user_note": _clean(previous.user_note, tag) if previous.user_note else None,
        "system_note": _clean(previous.system_note, tag) if previous.system_note else None,
    }


# (variable and tag name, label in cut notes, trimmer)
_Trimmer = Callable[[str, int, set[str]], Trimmed]
_SLOTS: tuple[tuple[str, str, _Trimmer], ...] = (
    ("claude_md", "CLAUDE.md", lambda text, room, _: keep_head(text, room, cap=CLAUDE_MD_CAP)),
    ("spec", "CONTEXT.md", lambda text, room, ws: select_spec(text, room, ticket_words=ws)),
    (
        "progress_log",
        "PROGRESS.md",
        lambda text, room, _: keep_newest_entries(text, room, cap=PROGRESS_CAP),
    ),
    (
        "decisions",
        "DECISIONS.md",
        lambda text, room, _: keep_newest_entries(text, room, cap=DECISIONS_CAP),
    ),
)


def _slot_sources(inputs: ContextInputs) -> dict[str, str | None]:
    docs = inputs.repo_docs
    progress, decisions = docs.progress_md, docs.decisions_md
    return {
        "claude_md": docs.claude_md,
        "spec": inputs.spec,
        "progress_log": newest_entries(progress, inputs.progress_entries) if progress else progress,
        "decisions": newest_lines(decisions, inputs.decisions_lines) if decisions else decisions,
    }


def build_implementer_prompt(
    inputs: ContextInputs, *, override_dir: Path | None = None
) -> RenderedPrompt:
    """The implementer agent's prompt for ``inputs``, within ``inputs.max_chars``.

    ``override_dir`` is the workspace's ``prompts/`` folder; its ``implementer.md.j2``
    replaces the default template if it exists. Raises ContextBudgetError if the
    untrimmable parts alone leave less than 2,000 characters for the rest, and
    PromptTemplateError for a broken override.
    """
    template = PromptTemplate(IMPLEMENTER_TEMPLATE, override_dir=override_dir)
    variables: dict[str, Any] = {
        "ticket": _ticket_vars(inputs),
        "previous": _previous_vars(inputs.previous),
        "commands": [
            (normalize_newlines(name), normalize_newlines(command))
            for name, command in inputs.commands.items()
        ],
        "read_only_git": list(READ_ONLY_GIT),
        **{name: None for name, _, _ in _SLOTS},
    }
    current = len(template.render(variables))
    if inputs.max_chars - current < MIN_CONTEXT_ROOM:
        raise ContextBudgetError(
            f"ticket {inputs.ticket.id} needs {current:,} characters before any context; "
            "raise context.max_chars in project.yaml"
        )

    ticket_words = words(f"{inputs.ticket.title}\n{inputs.ticket.body}")
    sources = _slot_sources(inputs)
    cuts: list[str] = []
    for name, label, trim in _SLOTS:
        raw = sources[name]
        if raw is None:
            continue
        text = _clean(raw, name)
        if not text.strip():
            continue
        # The block's own lines (tags, fence, heading), measured with the whole text.
        with_all = len(template.render({**variables, name: {"text": text, "note": None}}))
        room = inputs.max_chars - current - (with_all - current - len(text))
        # The estimate can be a few characters off once a cut changes the blank lines
        # around the text; shrink the room by the overshoot and try again.
        for _ in range(_FIT_ATTEMPTS):
            trimmed = trim(text, room, ticket_words)
            candidate = {**variables, name: {"text": trimmed.text, "note": trimmed.note}}
            size = len(template.render(candidate))
            if not trimmed.text.strip() or size <= inputs.max_chars:
                break
            room -= size - inputs.max_chars
        if not trimmed.text.strip() or size > inputs.max_chars:
            cuts.append(f"{label}: [trimmed: left out, no room]")
            continue
        if trimmed.note is not None:
            cuts.append(f"{label}: {trimmed.note}")
        variables = candidate
        current = size

    text = template.render(variables)
    if len(text) > inputs.max_chars:
        raise ContextBudgetError(
            f"{template.filename}: the prompt has {len(text):,} characters, more than "
            f"context.max_chars ({inputs.max_chars:,}); check the template"
        )
    return RenderedPrompt(text=text, chars=len(text), cuts=tuple(cuts), template=template.label)
