import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import app, plan
from spoolhq.services.agents import FakeRunner
from tests.conftest import DASHBOARD_PLAN, FIXTURES_DIR, dashboard_plan, plan_transcript

runner = CliRunner()

TICKET = """\
---
id: {id}
title: Ticket {id}
phase: 0
depends_on: [{deps}]
status: {status}
estimate_h: 1
---

## Done when
- [ ] It works
"""


def write(tickets: Path, ticket_id: str, deps: str = "", status: str = "ready") -> Path:
    path = tickets / f"{ticket_id}-x.md"
    path.write_text(TICKET.format(id=ticket_id, deps=deps, status=status), encoding="utf-8")
    return path


def make_project(projects_dir: Path, name: str = "demo") -> Path:
    tickets = projects_dir / name / "tickets"
    tickets.mkdir(parents=True)
    return tickets


def copy_dashboard(projects_dir: Path) -> Path:
    shutil.copytree(FIXTURES_DIR / "dashboard", projects_dir / "dashboard")
    return projects_dir / "dashboard" / "tickets"


def set_status(*args: str) -> tuple[int, str]:
    result = runner.invoke(app, ["tickets", "set-status", *args])
    return result.exit_code, result.output


# plan check ---------------------------------------------------------------------------


def test_check_valid_plan(projects_dir: Path) -> None:
    copy_dashboard(projects_dir)
    result = runner.invoke(app, ["plan", "check", "dashboard"])
    assert result.exit_code == 0, result.output
    assert result.output == "plan is valid (18 tickets)\n"


def test_check_reports_problems_and_invalid_files(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01", "T02")
    write(tickets, "T02", "T01")
    write(tickets, "T03", "T99")
    (tickets / "T04-broken.md").write_text("no frontmatter\n", encoding="utf-8")
    result = runner.invoke(app, ["plan", "check", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "Plan problems (2):",
        "  T03 depends on T99, which does not exist",
        "  cycle: T01 → T02 → T01",
        "",
        "Invalid ticket files (1):",
        "  tickets/T04-broken.md: line 1: the file must start with a '---' line opening the "
        "frontmatter",
    ]


def test_check_invalid_files_only(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01")
    (tickets / "notes.md").write_text("---\nid: T02\n---\n", encoding="utf-8")
    result = runner.invoke(app, ["plan", "check", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines()[0] == "Invalid ticket files (1):"


def test_check_one_ticket_and_unknown_project(projects_dir: Path) -> None:
    write(make_project(projects_dir), "T01")
    assert runner.invoke(app, ["plan", "check", "demo"]).output == "plan is valid (1 ticket)\n"
    result = runner.invoke(app, ["plan", "check", "nope"])
    assert result.exit_code == 1
    assert "error: no project 'nope'" in result.output


# plan next ----------------------------------------------------------------------------


def test_next_on_the_dashboard(projects_dir: Path) -> None:
    copy_dashboard(projects_dir)
    result = runner.invoke(app, ["plan", "next", "dashboard"])
    assert result.exit_code == 0, result.output
    assert result.output == "T01 · Repository and tooling\n"

    assert set_status("dashboard", "T01", "running")[0] == 0
    result = runner.invoke(app, ["plan", "next", "dashboard"])
    assert result.exit_code == 0
    assert result.output == "nothing to run: T01 is running\n"

    assert set_status("dashboard", "T01", "done")[0] == 0
    assert runner.invoke(app, ["plan", "next", "dashboard"]).output == "T02 · Backend scaffold\n"


def test_next_refuses_an_invalid_plan(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01", "T02")
    write(tickets, "T02", "T01")
    result = runner.invoke(app, ["plan", "next", "demo"])
    assert result.exit_code == 1
    assert result.output == "error: the plan has problems:\n  cycle: T01 → T02 → T01\n"


def test_next_refuses_invalid_files(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01")
    (tickets / "T02-broken.md").write_text("no frontmatter\n", encoding="utf-8")
    result = runner.invoke(app, ["plan", "next", "demo"])
    assert result.exit_code == 1
    lines = result.output.splitlines()
    assert lines[0] == "Invalid ticket files (1):"
    assert lines[-1] == "Fix them first (spool plan check)."


# plan summary -------------------------------------------------------------------------


def test_summary_of_the_dashboard(projects_dir: Path) -> None:
    copy_dashboard(projects_dir)
    result = runner.invoke(app, ["plan", "summary", "dashboard"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "draft:             0",
        "ready:             18",
        "running:           0",
        "awaiting_approval: 0",
        "blocked:           0",
        "done:              0",
        "",
        "remaining:     38.5h",
        "critical path: T01 → T02 → T04 → T07 → T08 → T11 → T12 → T15 → T16 → T17 → T18 (23h)",
    ]


def test_summary_when_all_done_and_invalid(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01", status="done")
    result = runner.invoke(app, ["plan", "summary", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[-2:] == ["remaining:     0h", "critical path: none"]

    write(tickets, "T02", "T03")
    result = runner.invoke(app, ["plan", "summary", "demo"])
    assert result.exit_code == 1
    assert "T02 depends on T03, which does not exist" in result.output


# tickets set-status -------------------------------------------------------------------


def test_set_status_changes_only_the_status_line(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    path = tickets / "T01-repository-and-tooling.md"
    before = path.read_text(encoding="utf-8")
    assert set_status("dashboard", "T01", "running") == (0, "T01: ready → running\n")
    assert path.read_text(encoding="utf-8") == before.replace(
        "status: ready\n", "status: running\n"
    )
    assert set_status("dashboard", "T01", "running") == (0, "T01 is already running\n")


def test_set_status_refusals(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    before = {path.name: path.read_bytes() for path in tickets.iterdir()}
    assert set_status("dashboard", "T02", "running") == (
        1,
        "error: T02 cannot start: waits for T01\n",
    )
    code, output = set_status("dashboard", "T01", "done")
    assert code == 1
    assert output == (
        "error: T01: ready → done is not allowed; from ready a ticket can move to draft or "
        "running\n"
    )
    code, output = set_status("dashboard", "T01", "doing")
    assert code == 1
    assert output.startswith("error: unknown status 'doing'")
    code, output = set_status("dashboard", "T42", "ready")
    assert (code, output) == (1, "error: no ticket T42 in project 'dashboard'\n")
    assert {path.name: path.read_bytes() for path in tickets.iterdir()} == before


def test_set_status_blocked_cannot_jump_to_done(projects_dir: Path) -> None:
    write(make_project(projects_dir), "T01", status="blocked")
    code, output = set_status("demo", "T01", "done")
    assert code == 1
    assert "T01: blocked → done is not allowed" in output


def test_set_status_on_an_invalid_file(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    (tickets / "T01-x.md").write_text(
        TICKET.format(id="T01", deps="", status="ready").replace("phase: 0", "phase: x"),
        encoding="utf-8",
    )
    code, output = set_status("demo", "T01", "draft")
    assert code == 1
    assert output.startswith("tickets/T01-x.md: phase:")


# plan generate / show / approve ---------------------------------------------------------


def use_planner(monkeypatch: pytest.MonkeyPatch, *transcripts: Path) -> FakeRunner:
    planner = FakeRunner(list(transcripts))
    monkeypatch.setattr(plan, "make_runner", lambda project: planner)
    return planner


def test_generate_prints_the_summary(plan_project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_planner(monkeypatch, DASHBOARD_PLAN)
    result = runner.invoke(app, ["plan", "generate", "demo"])

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0] == "wrote 18 draft tickets (39.5h)"
    assert lines[1].startswith("critical path: T01 → T02 → T04 → T07 → T08")
    assert lines[2:4] == ["problems:", "  none"]
    assert lines[-1] == "review the drafts (spool plan show demo), then: spool plan approve demo"


def test_generate_passes_the_template_description(
    plan_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    planner = use_planner(monkeypatch, DASHBOARD_PLAN)
    description = tmp_path / "template.md"
    description.write_text("FastAPI and React, CI included.", encoding="utf-8")

    result = runner.invoke(
        app, ["plan", "generate", "demo", "--template-description", str(description)]
    )

    assert result.exit_code == 0, result.output
    assert "FastAPI and React, CI included." in planner.calls[0][0]


def test_generate_reports_kept_and_deleted_tickets(
    plan_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    use_planner(monkeypatch, DASHBOARD_PLAN)
    assert runner.invoke(app, ["plan", "generate", "demo"]).exit_code == 0
    edited = plan_project / "tickets" / "T05-assessment-logic.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nnote\n", encoding="utf-8")
    data = dashboard_plan()
    data["tickets"] = [t for t in data["tickets"] if t["id"] not in ("T05", "T18")]
    use_planner(monkeypatch, plan_transcript(tmp_path / "again.jsonl", data))

    result = runner.invoke(app, ["plan", "generate", "demo"])

    assert result.exit_code == 0, result.output
    assert "kept: T05\ndeleted: T18\n" in result.stdout


def test_generate_fails_on_invalid_output(
    plan_project: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad = plan_transcript(tmp_path / "bad.jsonl", "nothing")
    use_planner(monkeypatch, bad, bad)

    result = runner.invoke(app, ["plan", "generate", "demo"])

    assert result.exit_code == 1
    assert "error: planner output invalid: no <plan> block in the final message" in result.stderr
    assert list((plan_project / "tickets").iterdir()) == []


def test_generate_fails_without_a_spec(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (workspace / "CONTEXT.md").unlink()
    use_planner(monkeypatch, DASHBOARD_PLAN)
    result = runner.invoke(app, ["plan", "generate", "demo"])
    assert result.exit_code == 1
    assert "error: no CONTEXT.md in" in result.stderr


def test_show_lists_the_drafts_and_the_problems(
    plan_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert "no draft tickets" in runner.invoke(app, ["plan", "show", "demo"]).stdout
    use_planner(monkeypatch, DASHBOARD_PLAN)
    runner.invoke(app, ["plan", "generate", "demo"])

    result = runner.invoke(app, ["plan", "show", "demo"])

    assert result.exit_code == 0, result.output
    lines = result.stdout.splitlines()
    assert lines[0].split() == ["ID", "ESTIMATE", "DEPENDS", "ON", "TITLE"]
    assert lines[7].split()[:5] == ["T07", "3h", "T04,", "T05,", "T06"]
    assert "18 drafts, 39.5h" in lines
    assert lines[-2:] == ["problems:", "  none"]

    write(plan_project / "tickets", "T19", "T99", status="draft")
    shown = runner.invoke(app, ["plan", "show", "demo"]).stdout
    assert "  T19 depends on T99, which does not exist" in shown


def test_approve_moves_the_drafts_then_has_nothing_to_approve(
    plan_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_planner(monkeypatch, DASHBOARD_PLAN)
    runner.invoke(app, ["plan", "generate", "demo"])

    result = runner.invoke(app, ["plan", "approve", "demo"])
    assert result.exit_code == 0, result.output
    assert result.stdout.startswith("approved 18 tickets: T01, T02, T03")

    again = runner.invoke(app, ["plan", "approve", "demo"])
    assert (again.exit_code, again.stderr) == (1, "error: nothing to approve\n")


def test_approve_refuses_a_cycle(plan_project: Path) -> None:
    tickets = plan_project / "tickets"
    write(tickets, "T01", "T02", status="draft")
    write(tickets, "T02", "T01", status="draft")

    result = runner.invoke(app, ["plan", "approve", "demo"])

    assert result.exit_code == 1
    assert result.stderr == "error: cannot approve the plan: cycle: T01 → T02 → T01\n"
