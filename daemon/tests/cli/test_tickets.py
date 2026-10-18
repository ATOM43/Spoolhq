import shutil
from pathlib import Path

from typer.testing import CliRunner

from spoolhq.cli import app
from tests.conftest import FIXTURES_DIR

runner = CliRunner()

TICKET = """\
---
id: {id}
title: {title}
phase: {phase}
depends_on: {deps}
status: {status}
estimate_h: {estimate}
---

## Scope
- Something.

## Done when
- [ ] First
- [x] Second
"""


def ticket(
    id: str = "T01",
    title: str = "First ticket",
    phase: int = 0,
    deps: str = "[]",
    status: str = "ready",
    estimate: str = "1.5",
) -> str:
    return TICKET.format(
        id=id, title=title, phase=phase, deps=deps, status=status, estimate=estimate
    )


def make_project(projects_dir: Path, files: dict[str, str], name: str = "demo") -> Path:
    tickets = projects_dir / name / "tickets"
    tickets.mkdir(parents=True)
    for file_name, text in files.items():
        (tickets / file_name).write_text(text, encoding="utf-8", newline="")
    return tickets


def test_list_prints_a_table(projects_dir: Path) -> None:
    make_project(
        projects_dir,
        {
            "T02-second.md": ticket("T02", "Second, longer title", 1, "[T01]", "draft", "2"),
            "T01-first.md": ticket(),
        },
    )
    result = runner.invoke(app, ["tickets", "list", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "ID   STATUS  PHASE  TITLE                 DEPENDS ON  ESTIMATE",
        "T01  ready   0      First ticket          -           1.5h",
        "T02  draft   1      Second, longer title  T01         2h",
    ]


def test_list_dashboard_plan(projects_dir: Path) -> None:
    shutil.copytree(FIXTURES_DIR / "dashboard", projects_dir / "dashboard")
    result = runner.invoke(app, ["tickets", "list", "dashboard"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert len(lines) == 19
    assert lines[0].split() == ["ID", "STATUS", "PHASE", "TITLE", "DEPENDS", "ON", "ESTIMATE"]
    assert [line.split()[0] for line in lines[1:]] == [f"T{n:02d}" for n in range(1, 19)]
    assert lines[7].split("  ")[0] == "T07"
    assert "Ingestion and sync" in lines[7]
    assert "T04, T05, T06" in lines[7]
    assert lines[7].endswith("3h")

    phase = runner.invoke(app, ["tickets", "list", "dashboard", "--phase", "3"])
    assert phase.exit_code == 0, phase.output
    assert [line.split()[0] for line in phase.output.splitlines()[1:]] == [
        "T11",
        "T12",
        "T13",
        "T14",
        "T15",
    ]

    both = runner.invoke(app, ["tickets", "list", "dashboard", "--status", "ready", "--phase", "0"])
    assert [line.split()[0] for line in both.output.splitlines()[1:]] == ["T01", "T02", "T03"]


def test_list_no_match(projects_dir: Path) -> None:
    make_project(projects_dir, {"T01-first.md": ticket()})
    result = runner.invoke(app, ["tickets", "list", "demo", "--status", "done"])
    assert result.exit_code == 0
    assert result.output == "No tickets match.\n"


def test_list_empty_project(projects_dir: Path) -> None:
    make_project(projects_dir, {})
    result = runner.invoke(app, ["tickets", "list", "demo"])
    assert result.exit_code == 0
    assert result.output == "No tickets in 'demo' yet.\n"


def test_list_unknown_status(projects_dir: Path) -> None:
    make_project(projects_dir, {})
    result = runner.invoke(app, ["tickets", "list", "demo", "--status", "doing"])
    assert result.exit_code == 1
    assert "error: unknown status 'doing'; expected one of: draft, ready," in result.output


def test_list_missing_project(projects_dir: Path) -> None:
    result = runner.invoke(app, ["tickets", "list", "nope"])
    assert result.exit_code == 1
    assert f"error: no project 'nope' in {projects_dir}" in result.output


def test_list_reports_invalid_files_last(projects_dir: Path) -> None:
    make_project(
        projects_dir,
        {
            "T01-first.md": ticket(),
            "T02-bad.md": ticket("T02", status="doing", estimate="50"),
            "notes.md": "no frontmatter\n",
        },
    )
    result = runner.invoke(app, ["tickets", "list", "demo"])
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "ID   STATUS  PHASE  TITLE         DEPENDS ON  ESTIMATE",
        "T01  ready   0      First ticket  -           1.5h",
        "",
        "Invalid tickets (2):",
        "  tickets/T02-bad.md: status: must be one of draft, ready, running, "
        "awaiting_approval, blocked, done",
        "  tickets/T02-bad.md: estimate_h: must be at most 40",
        "  tickets/notes.md: file name must be <id>-<slug>.md, like T04-project-workspace.md",
        "  tickets/notes.md: line 1: the file must start with a '---' line opening the frontmatter",
    ]


def test_list_only_invalid_files(projects_dir: Path) -> None:
    make_project(projects_dir, {"T02-bad.md": ticket("T02", deps="[T02]")})
    result = runner.invoke(app, ["tickets", "list", "demo", "--status", "done"])
    assert result.exit_code == 1
    assert result.output.splitlines() == [
        "Invalid tickets (1):",
        "  tickets/T02-bad.md: depends_on: T02 cannot depend on itself",
    ]


def test_show_prints_fields_checklist_and_body(projects_dir: Path) -> None:
    shutil.copytree(FIXTURES_DIR / "dashboard", projects_dir / "dashboard")
    result = runner.invoke(app, ["tickets", "show", "dashboard", "T07"])
    assert result.exit_code == 0, result.output
    assert result.output == (
        "id:              T07\n"
        "title:           Ingestion and sync\n"
        "phase:           1\n"
        "depends_on:      T04, T05, T06\n"
        "status:          ready\n"
        "estimate_h:      3\n"
        "review_required: false\n"
        "tracker_ref:     null\n"
        "\n"
        "Done when:\n"
        "  [ ] Re-running the import changes nothing\n"
        "  [ ] A changed file updates its rows\n"
        "\n"
        "--- T07-ingestion-and-sync.md ---\n"
        "## Scope\n"
        "- Import CSV folders into the database and keep them in sync.\n"
        "\n"
        "## Done when\n"
        "- [ ] Re-running the import changes nothing\n"
        "- [ ] A changed file updates its rows\n"
    )


def test_show_checked_items_and_tracker_ref(projects_dir: Path) -> None:
    shutil.copytree(FIXTURES_DIR / "tickets", projects_dir / "rt" / "tickets")
    result = runner.invoke(app, ["tickets", "show", "rt", "T08"])
    assert result.exit_code == 0, result.output
    assert "review_required: false\ntracker_ref:     CU-8x2\n" in result.output
    crlf = runner.invoke(app, ["tickets", "show", "rt", "T02"])
    assert "  [ ] CRLF survives a save\n  [x] Capital X counts as checked\n" in crlf.output
    assert "\r" not in crlf.output
    flagged = runner.invoke(app, ["tickets", "show", "rt", "T05"])
    assert "review_required: true\n" in flagged.output


def test_show_warns_without_done_when(projects_dir: Path) -> None:
    shutil.copytree(FIXTURES_DIR / "tickets", projects_dir / "rt" / "tickets")
    result = runner.invoke(app, ["tickets", "show", "rt", "T11"])
    assert result.exit_code == 0, result.output
    assert "Done when:\n  (none)\n" in result.stdout
    assert result.stderr == (
        "warning: tickets/T11-frontmatter-only.md: no '## Done when' section\n"
    )


def test_show_invalid_ticket(projects_dir: Path) -> None:
    make_project(projects_dir, {"T01-first.md": ticket(phase=-1)})
    result = runner.invoke(app, ["tickets", "show", "demo", "T01"])
    assert result.exit_code == 1
    assert result.output == "tickets/T01-first.md: phase: must be at least 0\n"


def test_show_missing_ticket(projects_dir: Path) -> None:
    make_project(projects_dir, {})
    result = runner.invoke(app, ["tickets", "show", "demo", "T09"])
    assert result.exit_code == 1
    assert result.output == "error: no ticket T09 in project 'demo'\n"
