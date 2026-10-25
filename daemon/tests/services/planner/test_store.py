import json
import threading
from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.planner import (
    PlannedTicket,
    PlannerError,
    approve_plan,
    generate_plan,
    load_existing,
    render_draft,
    store,
    write_plan,
)
from spoolhq.services.tickets import list_tickets, parse_ticket, render_ticket
from tests.conftest import DASHBOARD_PLAN, dashboard_plan


def make_plan(projects_dir: Path, home: Path) -> None:
    result = generate_plan(
        "demo",
        FakeRunner(DASHBOARD_PLAN),
        projects_dir=projects_dir,
        home=home,
        cancel=threading.Event(),
    )
    assert result.error is None, result.error


def write(tickets: Path, ticket_id: str, deps: str = "[]", status: str = "draft") -> Path:
    path = tickets / f"{ticket_id}-x.md"
    path.write_text(
        f"---\nid: {ticket_id}\ntitle: {ticket_id}\nphase: 0\ndepends_on: {deps}\n"
        f"status: {status}\nestimate_h: 2\n---\n\n## Done when\n- [ ] ok\n",
        encoding="utf-8",
    )
    return path


def test_a_draft_round_trips_through_the_ticket_store() -> None:
    planned = PlannedTicket.model_validate_json(json.dumps(dashboard_plan()["tickets"][6]))
    text = render_draft(planned, "just test")
    ticket = parse_ticket(text, "T07-ingestion-and-sync.md")

    assert render_ticket(ticket) == text
    assert text.startswith(
        "---\nid: T07\ntitle: Ingestion and sync\nphase: 1\ndepends_on: [T04, T05, T06]\n"
        "status: draft\nestimate_h: 3\nreview_required: false\n---\n\n## Purpose\n"
    )
    assert [item.text for item in ticket.done_when] == [
        "Re-running the import changes nothing",
        "A changed file updates its rows",
        "`just test` passes",
    ]


def test_a_title_that_needs_quotes_stays_valid_yaml() -> None:
    data = dashboard_plan()["tickets"][0] | {"title": "Fix: 'quotes' # and: colons"}
    text = render_draft(PlannedTicket.model_validate_json(json.dumps(data)), "just test")
    assert parse_ticket(text, "T01-x.md").meta.title == "Fix: 'quotes' # and: colons"


# writing ------------------------------------------------------------------------------


def test_a_failed_write_leaves_the_old_files(
    plan_project: Path, projects_dir: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_plan(projects_dir, home)
    tickets = plan_project / "tickets"
    before = {p.name: p.read_bytes() for p in tickets.iterdir()}
    record = (plan_project / store.PLAN_FILE).read_bytes()
    existing = load_existing("demo", projects_dir=projects_dir)
    drafts = {"T01-new.md": "new\n", "T02-new.md": "new\n"}
    real_replace = Path.replace
    calls = []

    def flaky(self: Path, target: Path) -> Path:
        calls.append(self)
        if self.name == ".T02-new.md.plan-tmp":
            raise OSError("disk full")
        return real_replace(self, target)

    monkeypatch.setattr(Path, "replace", flaky)
    with pytest.raises(PlannerError, match="cannot write the plan; nothing changed: disk full"):
        write_plan("demo", drafts, existing, projects_dir=projects_dir)
    monkeypatch.undo()

    assert calls  # the swap had started
    assert {p.name: p.read_bytes() for p in tickets.iterdir()} == before
    assert (plan_project / store.PLAN_FILE).read_bytes() == record


def test_an_unreadable_plan_record_keeps_every_draft(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    make_plan(projects_dir, home)
    (plan_project / store.PLAN_FILE).write_text("{broken", encoding="utf-8")

    existing = load_existing("demo", projects_dir=projects_dir)

    assert existing.replaceable == ()
    assert len(existing.kept) == 18


# approval -----------------------------------------------------------------------------


def test_approval_refuses_a_cycle_and_names_its_members(
    plan_project: Path, projects_dir: Path
) -> None:
    tickets = plan_project / "tickets"
    write(tickets, "T01", "[T03]")
    write(tickets, "T02", "[T01]")
    write(tickets, "T03", "[T02]")
    before = {p.name: p.read_bytes() for p in tickets.iterdir()}

    with pytest.raises(PlannerError) as info:
        approve_plan("demo", projects_dir=projects_dir)

    assert str(info.value) == "cannot approve the plan: cycle: T01 → T02 → T03 → T01"
    assert {p.name: p.read_bytes() for p in tickets.iterdir()} == before


def test_approval_names_every_problem(plan_project: Path, projects_dir: Path) -> None:
    tickets = plan_project / "tickets"
    write(tickets, "T01", "[T09]")
    (tickets / "T02-bad.md").write_text("nothing\n", encoding="utf-8")

    with pytest.raises(PlannerError) as info:
        approve_plan("demo", projects_dir=projects_dir)

    message = str(info.value)
    assert "T01 depends on T09, which does not exist" in message
    assert "tickets/T02-bad.md: line 1" in message


def test_approving_twice_gives_nothing_to_approve(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    make_plan(projects_dir, home)
    assert len(approve_plan("demo", projects_dir=projects_dir)) == 18
    with pytest.raises(PlannerError, match="^nothing to approve$"):
        approve_plan("demo", projects_dir=projects_dir)


def test_approval_moves_only_drafts_and_changes_only_the_status_line(
    plan_project: Path, projects_dir: Path
) -> None:
    tickets = plan_project / "tickets"
    done = write(tickets, "T01", status="done")
    draft = write(tickets, "T02", "[T01]")
    done_bytes, draft_text = done.read_bytes(), draft.read_text(encoding="utf-8")

    assert approve_plan("demo", projects_dir=projects_dir) == ("T02",)

    assert done.read_bytes() == done_bytes
    assert draft.read_text(encoding="utf-8") == draft_text.replace("status: draft", "status: ready")
    assert [t.meta.status for t in list_tickets("demo", projects_dir=projects_dir).tickets] == [
        "done",
        "ready",
    ]


def test_approval_of_an_unknown_project_fails(projects_dir: Path) -> None:
    projects_dir.mkdir()
    with pytest.raises(PlannerError, match="no project 'nope'"):
        approve_plan("nope", projects_dir=projects_dir)
