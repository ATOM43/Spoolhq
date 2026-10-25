"""Draft ticket files, the hashes that tell which drafts the user edited, and approval.

``<workspace>/.spoolhq/plan.json`` records the SHA-256 of every draft the planner wrote.
On a re-plan a draft whose file still has that hash is the planner's to replace; every
other ticket (edited or hand-made drafts, anything not in ``draft``) is kept byte for
byte. Writes are all-or-nothing: every file is staged next to its target first, and an
error while swapping them in puts the old files back.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from spoolhq.core.ids import id_key, slugify
from spoolhq.services.planner.model import PlannedTicket, PlannerError
from spoolhq.services.projects import project_dir
from spoolhq.services.projects.yaml_io import dump, to_node
from spoolhq.services.scheduler import SchedulerError, check_transition, validate_plan
from spoolhq.services.tickets import Ticket, TicketError, list_tickets, render_ticket, tickets_dir
from spoolhq.services.tickets.errors import source_name

PLAN_FILE = ".spoolhq/plan.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def done_when_items(planned: PlannedTicket, test_command: str) -> tuple[str, ...]:
    """The ticket's items, ending with `` `<test command>` passes`` (added if missing)."""
    last = f"`{test_command}` passes"
    items = planned.done_when
    return items if items[-1] == last else (*items, last)


def draft_file_name(planned: PlannedTicket) -> str:
    return f"{planned.id}-{slugify(planned.title)}.md"


def render_draft(planned: PlannedTicket, test_command: str) -> str:
    """The text of a ``draft`` ticket file that round-trips through the tickets store."""
    estimate = planned.estimate_h
    frontmatter = {
        "id": planned.id,
        "title": planned.title,
        "phase": planned.phase,
        "depends_on": list(planned.depends_on),
        "status": "draft",
        "estimate_h": int(estimate) if estimate.is_integer() else estimate,
        "review_required": planned.review_required,
    }
    lines = ["## Purpose", planned.purpose, "", "## Scope"]
    lines += [f"- {item}" for item in planned.scope]
    lines += ["", "## Done when"]
    lines += [f"- [ ] {item}" for item in done_when_items(planned, test_command)]
    return f"---\n{dump(to_node(frontmatter))}---\n\n" + "\n".join(lines) + "\n"


# --- what a re-plan may replace ---------------------------------------------------------


@dataclass(frozen=True)
class Existing:
    """A project's tickets, split into those kept as they are and those a plan replaces."""

    kept: tuple[Ticket, ...]
    replaceable: tuple[Ticket, ...]
    """Drafts the planner wrote and nobody edited since."""


def _recorded(workspace: Path) -> dict[str, str]:
    """The hashes in ``plan.json``; a missing or unreadable file records nothing."""
    try:
        data = json.loads((workspace / PLAN_FILE).read_text(encoding="utf-8"))
        tickets = data["tickets"]
    except (OSError, ValueError, KeyError, TypeError):
        return {}
    if not isinstance(tickets, dict):
        return {}
    return {key: value for key, value in tickets.items() if isinstance(value, str)}


def load_existing(project: str, *, projects_dir: Path) -> Existing:
    """Split the project's tickets; raises PlannerError if any ticket file is invalid."""
    try:
        listing = list_tickets(project, projects_dir=projects_dir)
    except TicketError as exc:
        raise PlannerError(str(exc)) from exc
    if listing.invalid:
        problems = [error for ticket in listing.invalid for error in ticket.errors]
        raise PlannerError(
            "some ticket files are invalid; fix them first (spool plan check): "
            + "; ".join(problems)
        )
    folder = tickets_dir(project, projects_dir=projects_dir)
    recorded = _recorded(project_dir(project, projects_dir))
    kept: list[Ticket] = []
    replaceable: list[Ticket] = []
    for ticket in listing.tickets:
        current = sha256((folder / ticket.file_name).read_bytes())
        if ticket.meta.status == "draft" and recorded.get(ticket.id) == current:
            replaceable.append(ticket)
        else:
            kept.append(ticket)
    return Existing(tuple(kept), tuple(replaceable))


# --- writing ------------------------------------------------------------------------------


def _replace_all(writes: Mapping[Path, str], deletes: Sequence[Path]) -> None:
    """Write and delete every file, or change nothing.

    Each new text is staged as a hidden temp file next to its target (the tickets store
    ignores hidden files); then the old files are moved aside and the staged ones
    renamed into place. Any error restores the old files.
    """
    staged: dict[Path, Path] = {}
    moved: dict[Path, Path] = {}
    placed: list[Path] = []
    try:
        for target, text in writes.items():
            temp = target.with_name(f".{target.name}.plan-tmp")
            staged[target] = temp
            temp.parent.mkdir(parents=True, exist_ok=True)
            temp.write_text(text, encoding="utf-8", newline="\n")
        for target in [*writes, *deletes]:
            if target.exists() and target not in moved:
                backup = target.with_name(f".{target.name}.plan-bak")
                target.replace(backup)
                moved[target] = backup
        for target, temp in staged.items():
            temp.replace(target)
            placed.append(target)
    except BaseException:
        for target in placed:
            target.unlink(missing_ok=True)
        for target, backup in moved.items():
            backup.replace(target)
        for temp in staged.values():
            temp.unlink(missing_ok=True)
        raise
    for backup in moved.values():
        backup.unlink(missing_ok=True)


def write_plan(
    project: str,
    drafts: Mapping[str, str],
    existing: Existing,
    *,
    projects_dir: Path,
    now: datetime | None = None,
) -> tuple[str, ...]:
    """Write ``drafts`` (file name → text), delete the replaceable drafts they don't
    overwrite, and record the new hashes in ``plan.json``. Returns the deleted ids."""
    folder = tickets_dir(project, projects_dir=projects_dir)
    workspace = project_dir(project, projects_dir)
    ids = {name.split("-", 1)[0]: name for name in drafts}
    gone = [ticket for ticket in existing.replaceable if ticket.file_name not in drafts]
    record = {
        "generated_at": (now or datetime.now(UTC)).isoformat(timespec="seconds"),
        "tickets": {
            ticket_id: sha256(drafts[ids[ticket_id]].encode("utf-8"))
            for ticket_id in sorted(ids, key=id_key)
        },
    }
    writes = {folder / name: text for name, text in drafts.items()}
    writes[workspace / PLAN_FILE] = json.dumps(record, indent=2) + "\n"
    try:
        _replace_all(writes, [folder / ticket.file_name for ticket in gone])
    except OSError as exc:
        raise PlannerError(f"cannot write the plan; nothing changed: {exc}") from exc
    return tuple(ticket.id for ticket in gone if ticket.id not in ids)


# --- approval -----------------------------------------------------------------------------


def approve_plan(project: str, *, projects_dir: Path) -> tuple[str, ...]:
    """Move every draft to ``ready`` in one step, after checking the whole plan.

    Raises PlannerError naming every problem (invalid files, plan problems, refused
    transitions), or ``nothing to approve`` when there are no drafts; then nothing
    changes. Returns the approved ids.
    """
    try:
        listing = list_tickets(project, projects_dir=projects_dir)
    except TicketError as exc:
        raise PlannerError(str(exc)) from exc
    problems = [error for ticket in listing.invalid for error in ticket.errors]
    problems += [problem.message for problem in validate_plan(listing.tickets)]
    drafts = [ticket for ticket in listing.tickets if ticket.meta.status == "draft"]
    if not problems and not drafts:
        raise PlannerError("nothing to approve")
    for ticket in drafts:
        try:
            check_transition(ticket, "ready", listing.tickets)
        except SchedulerError as exc:
            problems.append(str(exc))
    if problems:
        raise PlannerError("cannot approve the plan: " + "; ".join(problems))
    folder = tickets_dir(project, projects_dir=projects_dir)
    writes: dict[Path, str] = {}
    for ticket in drafts:
        ticket.meta.status = "ready"
        writes[folder / ticket.file_name] = render_ticket(ticket)
    try:
        _replace_all(writes, [])
    except OSError as exc:
        names = ", ".join(source_name(ticket.file_name) for ticket in drafts)
        raise PlannerError(f"cannot approve; nothing changed ({names}): {exc}") from exc
    return tuple(ticket.id for ticket in drafts)
