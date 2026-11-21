"""Adding tickets: the next ids, the files, and the checks an edit gets. One by hand, or
the planner's drafts together (refs ``D1`` to ``D3`` rewritten to their ids)."""

import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from spoolhq.core.daemon_lock import LockHeld, acquire_lock
from spoolhq.core.ids import TICKET_ID_RE, slugify
from spoolhq.services.git import GitError, run_git
from spoolhq.services.projects import ProjectError, edit_lock, load_project, project_dir
from spoolhq.services.projects.yaml_io import dump, to_node, write_atomic
from spoolhq.services.runs import RunLog, ticket_ids
from spoolhq.services.scheduler.errors import TicketEditError, TicketLockedError
from spoolhq.services.scheduler.graph import find_cycles
from spoolhq.services.tickets import (
    MAX_ESTIMATE_H,
    Ticket,
    list_tickets,
    parse_done_when,
    parse_ticket,
    tickets_dir,
)
from spoolhq.services.tickets.store import FILE_NAME_RE

LOCK_FILE = ".spoolhq/tickets.lock"
LOCK_WAIT_S = 10.0
LOCK_BUSY = "Another SpoolHQ process is adding a ticket; try again"
TAG_PREFIX = "ticket/"


class NewTicket(BaseModel):
    """What the Add ticket form and ``spool tickets new`` send. No id: the daemon
    assigns it."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(pattern=r"\S", max_length=200)
    scope: str = Field(default="", max_length=400_000)
    """Markdown; everything above the "Done when" heading."""
    done_when: str = Field(max_length=100_000)
    """The checklist as markdown, one ``- [ ] …`` line per item."""
    depends_on: list[str] = Field(default_factory=list)
    estimate_h: float = Field(default=1, gt=0, le=MAX_ESTIMATE_H, allow_inf_nan=False)
    review_required: bool = False
    phase: int | None = Field(default=None, ge=0)
    """Defaults to the highest phase the project has (0 without tickets)."""


class DraftTicket(NewTicket):
    """One planner draft as the user saves it: a ticket plus its ``ref``, which other
    drafts' ``depends_on`` may name."""

    ref: str = Field(pattern=r"^D[1-3]$")


@dataclass(frozen=True)
class TicketProblem:
    """Why a new ticket can't be saved, and the field to fix."""

    code: str
    """``unknown_dependency``, ``cycle`` or ``missing_done_when`` (drafts add more)."""
    message: str
    field: str


def ticket_problems(
    new: Mapping[str, tuple[Sequence[str], str]], plan: Sequence[Ticket]
) -> dict[str, list[TicketProblem]]:
    """The problems of new tickets added to ``plan``. ``new`` maps each new ticket's id
    (or ref) to its ``depends_on`` and body. A dependency must be a ticket of ``plan`` or
    another new one; a cycle is reported for every new ticket in it or depending on it.
    """
    known = {t.id for t in plan} | new.keys()
    deps = {t.id: set(t.meta.depends_on) for t in plan}
    deps.update((key, set(item[0]) & known) for key, item in new.items())
    cycles = find_cycles(deps)
    found: dict[str, list[TicketProblem]] = {}
    for key, (depends_on, body) in new.items():
        problems = found.setdefault(key, [])
        unknown = sorted(set(depends_on) - known)
        if unknown:
            message = f"depends on {', '.join(unknown)}, which does not exist"
            problems.append(TicketProblem("unknown_dependency", message, "depends_on"))
        for cycle in cycles:
            if {key, *depends_on} & set(cycle):
                message = "cycle: " + " → ".join([*cycle, cycle[0]])
                problems.append(TicketProblem("cycle", message, "depends_on"))
        if not parse_done_when(body)[0]:
            message = "“Done when” needs at least one checklist item"
            problems.append(TicketProblem("missing_done_when", message, "done_when"))
    return found


def _body(new: NewTicket) -> str:
    scope = new.scope.strip()
    return (f"{scope}\n\n" if scope else "") + f"## Done when\n{new.done_when.strip()}\n"


@contextmanager
def tickets_lock(workspace: Path) -> Iterator[None]:
    """The OS lock ``spool tickets new`` and the daemon share; TicketLockedError after
    ``LOCK_WAIT_S``."""
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            lock = acquire_lock(workspace / LOCK_FILE)
            break
        except LockHeld:
            if time.monotonic() >= deadline:
                raise TicketLockedError(LOCK_BUSY) from None
            time.sleep(0.05)
    with lock:
        yield


def _used_ids(project: str, workspace: Path, *, projects_dir: Path) -> list[str]:
    """Ticket ids from the repo's ``ticket/TNN`` tags and the run log."""
    used: list[str] = []
    try:
        repo = load_project(project, projects_dir=projects_dir).repo_path
        tags = run_git(["tag", "--list", f"{TAG_PREFIX}*"], repo).check().stdout
        used += [line.strip().removeprefix(TAG_PREFIX) for line in tags.splitlines()]
    except (ProjectError, GitError):
        pass  # no readable settings or repo: nothing merged to count
    try:
        with RunLog.open_read_only(workspace) as log:
            used += ticket_ids(log)
    except FileNotFoundError:
        pass  # no run yet
    return used


def create_ticket(project: str, new: NewTicket, *, projects_dir: Path) -> Ticket:
    """Write a new ticket file with the number after the highest one in ``tickets/``
    (invalid files count too), the repo's ``ticket/TNN`` tags and the run log, so an id
    is never shared or reused, even after a ticket is deleted; a gap is never filled.

    ``ready``, or ``draft`` while a draft plan waits for approval, so it is approved
    with that plan. Refused before anything is written (TicketEditError naming the
    field) for an unknown dependency, a dependency that sits in a cycle, or no "Done
    when" items. The id is taken and the file written under the project's edit lock and
    the OS lock ``.spoolhq/tickets.lock`` (TicketLockedError if another process holds
    it for ``LOCK_WAIT_S``).
    """
    return _create(project, [new], projects_dir=projects_dir, batch=False)[0]


def create_tickets(
    project: str, drafts: Sequence[DraftTicket], *, projects_dir: Path
) -> list[Ticket]:
    """Write several drafts at once, like ``create_ticket``: ids in draft order, each
    ref in ``depends_on`` rewritten to its draft's id, the whole set checked, and every
    file written or none. A refusal's field is ``tickets.<index>.<field>``."""
    refs = [draft.ref for draft in drafts]
    for index, ref in enumerate(refs):
        if ref in refs[:index]:
            raise TicketEditError(f"{ref} appears more than once", f"tickets.{index}.ref")
    return _create(project, drafts, projects_dir=projects_dir, batch=True)


def _create(
    project: str, items: Sequence[NewTicket], *, projects_dir: Path, batch: bool
) -> list[Ticket]:
    folder = tickets_dir(project, projects_dir=projects_dir)
    workspace = project_dir(project, projects_dir)
    with edit_lock(workspace), tickets_lock(workspace):
        listing = list_tickets(project, projects_dir=projects_dir)
        plan = listing.tickets
        names = [t.file_name for t in plan] + [t.file_name for t in listing.invalid]
        prefixes = [m["prefix"] for name in names if (m := FILE_NAME_RE.fullmatch(name))]
        prefixes += _used_ids(project, workspace, projects_dir=projects_dir)
        highest = max((int(p[1:]) for p in prefixes if TICKET_ID_RE.fullmatch(p)), default=0)
        ids = [f"T{highest + n:02d}" for n in range(1, len(items) + 1)]
        real = {item.ref: ids[n] for n, item in enumerate(items) if isinstance(item, DraftTicket)}
        depends = [[real.get(dep, dep) for dep in item.depends_on] for item in items]

        found = ticket_problems(
            {ids[n]: (depends[n], _body(item)) for n, item in enumerate(items)}, plan
        )
        for n, ticket_id in enumerate(ids):
            if found[ticket_id]:
                first = found[ticket_id][0]
                field = f"tickets.{n}.{first.field}" if batch else first.field
                raise TicketEditError(first.message, field)

        status = "draft" if any(t.meta.status == "draft" for t in plan) else "ready"
        default_phase = max((t.meta.phase for t in plan), default=0)
        files: list[tuple[str, str]] = []
        tickets: list[Ticket] = []
        for n, item in enumerate(items):
            estimate = item.estimate_h
            frontmatter = {
                "id": ids[n],
                "title": item.title.strip(),
                "phase": item.phase if item.phase is not None else default_phase,
                "depends_on": depends[n],
                "status": status,
                "estimate_h": int(estimate) if float(estimate).is_integer() else estimate,
                "review_required": item.review_required,
            }
            text = f"---\n{dump(to_node(frontmatter))}---\n\n{_body(item)}"
            file_name = f"{ids[n]}-{slugify(item.title)}.md"
            tickets.append(parse_ticket(text, file_name))  # every TicketMeta rule, first
            files.append((file_name, text))
        folder.mkdir(exist_ok=True)
        written: list[Path] = []
        try:
            for file_name, text in files:
                write_atomic(folder / file_name, text)
                written.append(folder / file_name)
        except OSError:
            for path in written:
                path.unlink(missing_ok=True)
            raise
    return tickets
