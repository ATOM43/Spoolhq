"""``draft_tickets()``: one read-only planner run that turns a short request into 1 to 3
draft tickets, writing no files.

The agent's ``<drafts>`` block is untrusted. An answer whose shape can't be read (no
block, not JSON, not 1 to 3 drafts with refs ``D1``…) is retried once with the error,
then fails with ``UNREADABLE``. Anything wrong inside a readable draft (a field of the
wrong type, an unknown dependency, a cycle, an empty "Done when", more than 4 hours)
is a problem on that draft, for the user to fix before saving.
"""

import json
import re
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from spoolhq.core.tokens import weighted_tokens
from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentRunner,
    Budget,
    Outcome,
    RunResult,
    repo_settings_refusal,
)
from spoolhq.services.agents.runner import RawCallback
from spoolhq.services.planner.model import MAX_ESTIMATE_H, PlannerError, clean_title, one_line
from spoolhq.services.planner.planner import PLANNER_MAX_TURNS, PROMPTS_DIR, read_spec
from spoolhq.services.planner.prompt import render_draft_prompt
from spoolhq.services.projects import (
    NO_TEST_COMMAND,
    ProjectError,
    has_spec,
    load_project,
    project_dir,
)
from spoolhq.services.scheduler import TicketProblem, ticket_problems
from spoolhq.services.tickets import Ticket, TicketError, list_tickets

REQUEST_MAX = 2_000
MAX_DRAFTS = 3
UNREADABLE = "The planner's answer couldn't be read"

_BLOCK_RE = re.compile(r"<drafts>(.*?)</drafts>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"\A```[A-Za-z]*\n(.*)\n```\Z", re.DOTALL)
_STRINGS = TypeAdapter(list[str])
_FIELDS: dict[str, tuple[Callable[[Any], Any], Any]] = {
    # field: (validator, default when missing; None: required)
    "title": (TypeAdapter(str).validate_python, None),
    "scope": (TypeAdapter(str | list[str]).validate_python, None),
    "done_when": (_STRINGS.validate_python, None),
    "depends_on": (_STRINGS.validate_python, []),
    "estimate_h": (TypeAdapter(float, config={"allow_inf_nan": False}).validate_python, None),
    "review_required": (TypeAdapter(bool, config={"strict": True}).validate_python, False),
    "phase": (TypeAdapter(int, config={"strict": True}).validate_python, None),
}
_EMPTY = {"title": "", "scope": "", "done_when": [], "estimate_h": 0.0, "phase": 0}


def _ignore(_event: AgentEvent) -> None:
    pass


@dataclass(frozen=True)
class Draft:
    """One drafted ticket, cleaned; a field that couldn't be read is empty (and named by
    a ``schema`` problem)."""

    ref: str
    title: str
    scope: str
    """Markdown: the model's scope bullets as ``- …`` lines."""
    done_when: tuple[str, ...]
    depends_on: tuple[str, ...]
    """Existing ticket ids and other drafts' refs."""
    estimate_h: float
    review_required: bool
    phase: int
    problems: tuple[TicketProblem, ...]


@dataclass(frozen=True)
class DraftResult:
    """What one ``draft_tickets`` call did; ``error`` is None when drafts came back."""

    outcome: Outcome
    error: str | None
    drafts: tuple[Draft, ...]
    attempts: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cost_micro_usd: int | None


class UnreadableDrafts(PlannerError):
    """The answer's shape can't be read; the message says why, for the retry."""


def parse_drafts(final_text: str) -> list[dict[str, Any]]:
    """The drafts of the last ``<drafts>`` block; UnreadableDrafts if its shape is wrong."""
    blocks = _BLOCK_RE.findall(final_text)
    if not blocks:
        raise UnreadableDrafts("no <drafts> block in the final message")
    text = blocks[-1].strip()
    if fence := _FENCE_RE.match(text):
        text = fence[1].strip()
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UnreadableDrafts(f"the <drafts> block is not valid JSON: {exc}") from None
    drafts = raw.get("drafts") if isinstance(raw, dict) else None
    if not isinstance(drafts, list) or not 1 <= len(drafts) <= MAX_DRAFTS:
        raise UnreadableDrafts(f'the JSON needs "drafts": a list of 1 to {MAX_DRAFTS} objects')
    for index, draft in enumerate(drafts):
        if not isinstance(draft, dict) or draft.get("ref") != f"D{index + 1}":
            raise UnreadableDrafts(
                f'draft {index + 1} must be an object with "ref": "D{index + 1}"'
            )
    return drafts


def _read_fields(raw: dict[str, Any]) -> tuple[dict[str, Any], list[TicketProblem]]:
    """Each field validated alone, so one bad field doesn't hide the others."""
    values: dict[str, Any] = {}
    problems = [
        TicketProblem("schema", f"{key}: not a draft field", key)
        for key in raw
        if key != "ref" and key not in _FIELDS
    ]
    for key, (validate, default) in _FIELDS.items():
        if key not in raw:
            if default is None:
                problems.append(TicketProblem("schema", f"{key}: missing", key))
            values[key] = default if default is not None else _EMPTY[key]
            continue
        try:
            values[key] = validate(raw[key])
        except ValidationError as exc:
            problems.append(TicketProblem("schema", f"{key}: {exc.errors()[0]['msg']}", key))
            values[key] = default if default is not None else _EMPTY[key]
    if isinstance(raw.get("estimate_h"), bool):  # JSON true is not a number of hours
        problems.append(TicketProblem("schema", "estimate_h: not a number", "estimate_h"))
        values["estimate_h"] = 0.0
    return values, problems


def check_drafts(
    raw: Sequence[dict[str, Any]], plan: Sequence[Ticket], test_command: str
) -> tuple[Draft, ...]:
    """The drafts of a readable answer, cleaned, with their problems: like a plan, plus
    an estimate outside 0 to 4 h. A missing test-command item is appended (a non-empty
    "Done when" only), as the planner does (DECISIONS 211)."""
    test_item = f"`{test_command}` passes"
    read: list[tuple[str, dict[str, Any], list[TicketProblem]]] = []
    for item in raw:
        values, problems = _read_fields(item)
        scope = values["scope"]
        bullets = [scope] if isinstance(scope, str) else scope
        values["scope"] = "\n".join(f"- {line}" for b in bullets if (line := one_line(b)))
        values["title"] = clean_title(values["title"])
        values["done_when"] = [line for item in values["done_when"] if (line := one_line(item))]
        if values["done_when"] and values["done_when"][-1] != test_item:
            values["done_when"].append(test_item)
        values["depends_on"] = list(dict.fromkeys(dep.strip() for dep in values["depends_on"]))
        if not values["title"] and not any(p.field == "title" for p in problems):
            problems.append(TicketProblem("schema", "title: must not be empty", "title"))
        estimate = values["estimate_h"]
        if estimate > MAX_ESTIMATE_H:
            message = f"{estimate:g} h is over {MAX_ESTIMATE_H} h: split the work"
            problems.append(TicketProblem("estimate_too_high", message, "estimate_h"))
        elif estimate <= 0 and not any(p.field == "estimate_h" for p in problems):
            problems.append(TicketProblem("schema", "estimate_h: must be over 0", "estimate_h"))
        if values["phase"] < 0:
            problems.append(TicketProblem("schema", "phase: must be 0 or more", "phase"))
        read.append((item["ref"], values, problems))

    graph = {
        ref: (
            values["depends_on"],
            "## Done when\n" + "".join(f"- [ ] {i}\n" for i in values["done_when"]),
        )
        for ref, values, _ in read
    }
    found = ticket_problems(graph, plan)
    return tuple(
        Draft(
            ref=ref,
            title=values["title"],
            scope=values["scope"],
            done_when=tuple(values["done_when"]),
            depends_on=tuple(values["depends_on"]),
            estimate_h=values["estimate_h"],
            review_required=values["review_required"],
            phase=values["phase"],
            problems=(*problems, *found[ref]),
        )
        for ref, values, problems in read
    )


def draft_tickets(
    project: str,
    request: str,
    runner: AgentRunner,
    *,
    projects_dir: Path,
    home: Path,
    cancel: threading.Event,
    model: str | None = None,
    on_raw: RawCallback | None = None,
    code_map: str | None = None,
) -> DraftResult:
    """Draft tickets for ``request`` with the planner's policy, turns and budget.

    Raises PlannerError before the agent starts (bad project, no test command, invalid
    ticket files, repo agent settings) and whatever ``runner.run`` raises then;
    everything after the agent started is in the result.
    """
    try:
        settings = load_project(project, projects_dir=projects_dir)
        plan = list_tickets(project, projects_dir=projects_dir)
    except (ProjectError, TicketError) as exc:
        raise PlannerError(str(exc)) from exc
    if plan.invalid:
        names = ", ".join(invalid.file_name for invalid in plan.invalid)
        raise PlannerError(f"fix the invalid ticket files first: {names}")
    test_command = settings.commands.test
    if test_command is None:
        raise PlannerError(NO_TEST_COMMAND)
    workspace = project_dir(project, projects_dir)
    spec = read_spec(workspace) if has_spec(project, projects_dir=projects_dir) else None
    policy = AgentPolicy.read_only_for(settings.repo_path, home, role="planner")
    if refused := repo_settings_refusal(runner, settings.repo_path):
        raise PlannerError(refused)
    limit = settings.agents.budget_per_ticket
    results: list[RunResult] = []

    def finish(error: str | None, drafts: tuple[Draft, ...] = ()) -> DraftResult:
        costs = [r.cost_micro_usd for r in results if r.cost_micro_usd is not None]
        return DraftResult(
            outcome=results[-1].outcome,
            error=error,
            drafts=drafts,
            attempts=len(results),
            input_tokens=sum(r.input_tokens for r in results),
            output_tokens=sum(r.output_tokens for r in results),
            cache_read_tokens=sum(r.cache_read_tokens for r in results),
            cost_micro_usd=sum(costs) if costs else None,
        )

    final: list[str] = []

    def capture(message: dict[str, Any]) -> None:
        # The result's full final text; RunResult.summary keeps only its end.
        if message.get("type") == "result" and isinstance(message.get("result"), str):
            final.append(message["result"])
        if on_raw is not None:
            on_raw(message)

    error: str | None = None
    for _attempt in range(2):
        left = None
        if limit is not None and limit.tokens is not None:
            used = sum(
                weighted_tokens(r.input_tokens, r.output_tokens, r.cache_read_tokens)
                for r in results
            )
            if used >= limit.tokens:
                return finish(f"budget used up: {used:,} of {limit.tokens:,} weighted tokens")
            left = limit.tokens - used
        final.clear()
        prompt = render_draft_prompt(
            request,
            spec,
            plan.tickets,
            test_command,
            max_chars=settings.context.max_chars,
            previous_error=error,
            override_dir=workspace / PROMPTS_DIR,
            code_map=code_map,
            code_map_chars=settings.context.code_map_chars,
        )
        result = runner.run(
            prompt,
            policy,
            Budget(max_turns=PLANNER_MAX_TURNS, max_usd=None, max_tokens=left),
            model=model,
            on_event=_ignore,
            on_raw=capture,
            cancel=cancel,
        )
        results.append(result)
        if result.outcome is not Outcome.COMPLETED:
            detail = f": {result.error}" if result.error else ""
            return finish(f"planner run ended: {result.outcome.value}{detail}")
        try:
            raw = parse_drafts(final[-1] if final else result.summary)
        except UnreadableDrafts as exc:
            error = str(exc)
            continue
        return finish(None, check_drafts(raw, plan.tickets, test_command))
    return finish(UNREADABLE)
