"""The inputs of a prompt, as plain frozen values.

Callers build these from the ticket store and the project settings; this package
imports no other service package.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_MAX_CHARS = 120_000
DEFAULT_PROGRESS_ENTRIES = 3
DEFAULT_DECISIONS_LINES = 20
ATTEMPT_KINDS: tuple[str, ...] = ("gate_retry", "review_retry", "conflict_retry", "pr_changes")


@dataclass(frozen=True)
class DependencyView:
    id: str
    title: str
    status: str


@dataclass(frozen=True)
class TicketView:
    id: str
    title: str
    body: str
    """The ticket file's markdown body exactly as stored."""
    depends_on: tuple[DependencyView, ...] = ()
    review_required: bool = False


@dataclass(frozen=True)
class RepoDocs:
    """The repository's notes; ``None`` means the file does not exist."""

    claude_md: str | None = None
    progress_md: str | None = None
    decisions_md: str | None = None


@dataclass(frozen=True)
class GateFailure:
    command: str
    """The command as configured, e.g. ``just test``."""
    exit_code: int | None
    """``None`` when the command timed out."""
    timed_out: bool
    output_excerpt: str


@dataclass(frozen=True)
class ReviewNote:
    item: str
    """The "Done when" line."""
    met: bool
    reason: str


@dataclass(frozen=True)
class PreviousAttempt:
    kind: str
    """One of ``ATTEMPT_KINDS`` (T07's attempt kinds, as plain strings)."""
    number: int
    failing_tests: tuple[str, ...] = ()
    gate_failures: tuple[GateFailure, ...] = ()
    review_notes: tuple[ReviewNote, ...] = ()
    conflict_files: tuple[str, ...] = ()
    user_note: str | None = None
    """What the user wrote for this retry ("Note from the user")."""
    pr_review: str | None = None
    """The review that requested changes on the pull request (its body and inline
    comments), from GitHub: untrusted, shown in its own fenced block."""
    system_note: str | None = None
    """SpoolHQ's own explanation: a timeout, a turn limit, a conflict ("Note from SpoolHQ")."""

    def __post_init__(self) -> None:
        if self.kind not in ATTEMPT_KINDS:
            expected = ", ".join(ATTEMPT_KINDS)
            raise ValueError(f"unknown attempt kind {self.kind!r}; expected one of: {expected}")
        if self.number < 1:
            raise ValueError(f"attempt number must be at least 1, got {self.number}")


@dataclass(frozen=True)
class ContextInputs:
    ticket: TicketView
    spec: str | None
    """The workspace's ``CONTEXT.md``; ``None`` if it does not exist."""
    repo_docs: RepoDocs
    commands: Mapping[str, str] = field(default_factory=dict)
    """The project's stack commands, by name, in the order to list them."""
    previous: PreviousAttempt | None = None
    max_chars: int = DEFAULT_MAX_CHARS
    progress_entries: int = DEFAULT_PROGRESS_ENTRIES
    """The newest ``PROGRESS.md`` entries to include, before the character budget."""
    decisions_lines: int = DEFAULT_DECISIONS_LINES
    """The newest non-blank ``DECISIONS.md`` lines to include, before the budget."""

    def __post_init__(self) -> None:
        if self.max_chars < 1:
            raise ValueError(f"max_chars must be positive, got {self.max_chars}")
        if self.progress_entries < 1 or self.decisions_lines < 1:
            raise ValueError("progress_entries and decisions_lines must be positive")


@dataclass(frozen=True)
class RenderedPrompt:
    text: str
    chars: int
    cuts: tuple[str, ...]
    """One note per trimmed input, e.g. ``[trimmed: kept the last 12 of 104 entries]``."""
    template: str
    """``"default"``, or the override's path relative to the workspace."""
