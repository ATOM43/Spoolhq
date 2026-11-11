"""Adding a ticket by hand: the next id, the file, and the checks an edit gets."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from spoolhq.core.ids import TICKET_ID_RE, slugify
from spoolhq.services.projects import edit_lock, project_dir
from spoolhq.services.projects.yaml_io import dump, to_node, write_atomic
from spoolhq.services.scheduler.errors import TicketEditError
from spoolhq.services.scheduler.graph import validate_plan
from spoolhq.services.tickets import (
    MAX_ESTIMATE_H,
    Ticket,
    list_tickets,
    parse_done_when,
    parse_ticket,
    tickets_dir,
)
from spoolhq.services.tickets.store import FILE_NAME_RE


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


def _body(new: NewTicket) -> str:
    scope = new.scope.strip()
    return (f"{scope}\n\n" if scope else "") + f"## Done when\n{new.done_when.strip()}\n"


def create_ticket(project: str, new: NewTicket, *, projects_dir: Path) -> Ticket:
    """Write a new ticket file with the number after the highest one in ``tickets/``
    (invalid files count too, so no id is ever shared; a gap is never filled).

    ``ready``, or ``draft`` while a draft plan waits for approval, so it is approved
    with that plan. Refused before anything is written (TicketEditError naming the
    field) for an unknown dependency, a dependency that sits in a cycle, or no "Done
    when" items. The id is taken and the file written under the project's edit lock.
    """
    folder = tickets_dir(project, projects_dir=projects_dir)
    # shortcut: the lock is in-process (decision 297), so `spool tickets new` racing
    # the daemon could pick the same id; use an OS file lock if that ever happens.
    with edit_lock(project_dir(project, projects_dir)):
        listing = list_tickets(project, projects_dir=projects_dir)
        plan = listing.tickets
        names = [t.file_name for t in plan] + [t.file_name for t in listing.invalid]
        prefixes = [m["prefix"] for name in names if (m := FILE_NAME_RE.fullmatch(name))]
        highest = max((int(p[1:]) for p in prefixes if TICKET_ID_RE.fullmatch(p)), default=0)
        ticket_id = f"T{highest + 1:02d}"

        unknown = sorted(set(new.depends_on) - {t.id for t in plan})
        if unknown:
            raise TicketEditError(
                f"depends on {', '.join(unknown)}, which does not exist", "depends_on"
            )
        body = _body(new)
        if not parse_done_when(body)[0]:
            raise TicketEditError("“Done when” needs at least one checklist item", "done_when")
        for problem in validate_plan(plan):
            if problem.code == "cycle" and set(problem.ticket_ids) & set(new.depends_on):
                raise TicketEditError(problem.message, "depends_on")

        estimate = new.estimate_h
        frontmatter = {
            "id": ticket_id,
            "title": new.title.strip(),
            "phase": (
                new.phase if new.phase is not None else max((t.meta.phase for t in plan), default=0)
            ),
            "depends_on": list(new.depends_on),
            "status": "draft" if any(t.meta.status == "draft" for t in plan) else "ready",
            "estimate_h": int(estimate) if float(estimate).is_integer() else estimate,
            "review_required": new.review_required,
        }
        text = f"---\n{dump(to_node(frontmatter))}---\n\n{body}"
        file_name = f"{ticket_id}-{slugify(new.title)}.md"
        ticket = parse_ticket(text, file_name)  # every TicketMeta rule, before writing
        folder.mkdir(exist_ok=True)
        write_atomic(folder / file_name, text)
    return ticket
