"""`spool prompt show`."""

import shutil
from pathlib import Path

from typer.testing import CliRunner

from spoolhq.cli import app
from spoolhq.services.context import (
    ContextInputs,
    DependencyView,
    RepoDocs,
    TicketView,
    build_implementer_prompt,
)
from spoolhq.services.tickets import load_ticket
from tests.conftest import FIXTURES_DIR

runner = CliRunner()
CONTEXT = FIXTURES_DIR / "context"
T02 = """\
---
id: T02
title: Daemon and CLI scaffold
phase: 0
depends_on: []
status: done
estimate_h: 2
---

## Done when
- [x] It runs
"""


def add_tickets(workspace: Path) -> None:
    tickets = workspace / "tickets"
    tickets.mkdir(exist_ok=True)
    shutil.copyfile(CONTEXT / "T04.md", tickets / "T04-project-workspace-and-settings.md")
    (tickets / "T02-daemon-and-cli-scaffold.md").write_text(T02, encoding="utf-8")


def test_show_prints_the_prompt(workspace: Path, git_repo: Path, projects_dir: Path) -> None:
    add_tickets(workspace)
    shutil.copyfile(CONTEXT / "CLAUDE.md", git_repo / "CLAUDE.md")

    result = runner.invoke(app, ["prompt", "show", "demo", "T04"])

    assert result.exit_code == 0, result.stderr
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    expected = build_implementer_prompt(
        ContextInputs(
            ticket=TicketView(
                "T04",
                ticket.meta.title,
                ticket.body,
                (DependencyView("T02", "Daemon and CLI scaffold", "done"),),
            ),
            spec=(workspace / "CONTEXT.md").read_text(encoding="utf-8"),
            repo_docs=RepoDocs(claude_md=(CONTEXT / "CLAUDE.md").read_text(encoding="utf-8")),
            commands={"install": "just install", "lint": "just lint", "test": "just test"},
        )
    )
    assert result.stdout == expected.text
    assert result.stderr == f"template: default · {expected.chars:,} of 120,000 characters\n"
    assert str(git_repo) not in result.stdout


def test_show_reports_cuts_and_uses_an_override(workspace: Path, git_repo: Path) -> None:
    add_tickets(workspace)
    (git_repo / "CLAUDE.md").write_text("- rule\n" * 4_000, encoding="utf-8")
    (workspace / "prompts").mkdir()
    (workspace / "prompts" / "implementer.md.j2").write_text(
        "{{ ticket.id }}\n{{ claude_md.text if claude_md else '' }}\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["prompt", "show", "demo", "T04"])

    assert result.exit_code == 0, result.stderr
    assert result.stdout.startswith("T04\n- rule\n")
    lines = result.stderr.splitlines()
    assert lines[0].startswith("template: prompts/implementer.md.j2 · ")
    assert lines[1] == "CLAUDE.md: [trimmed: kept the first 15,995 of 28,000 characters]"


def test_unknown_ticket(workspace: Path) -> None:
    add_tickets(workspace)
    result = runner.invoke(app, ["prompt", "show", "demo", "T99"])
    assert result.exit_code == 1
    assert result.stdout == ""
    assert "ticket T99 not found in 'demo'" in result.stderr


def test_invalid_ticket_reports_its_errors(workspace: Path) -> None:
    add_tickets(workspace)
    path = workspace / "tickets" / "T04-project-workspace-and-settings.md"
    path.write_text(path.read_text(encoding="utf-8").replace("ready", "doing"), encoding="utf-8")
    result = runner.invoke(app, ["prompt", "show", "demo", "T04"])
    assert result.exit_code == 1
    assert "status: must be one of" in result.stderr


def test_unknown_project() -> None:
    result = runner.invoke(app, ["prompt", "show", "nope", "T04"])
    assert result.exit_code == 1
    assert "no project 'nope'" in result.stderr


def test_override_error_exits_1(workspace: Path) -> None:
    add_tickets(workspace)
    (workspace / "prompts").mkdir()
    (workspace / "prompts" / "implementer.md.j2").write_text("{{ nope }}\n", encoding="utf-8")
    result = runner.invoke(app, ["prompt", "show", "demo", "T04"])
    assert result.exit_code == 1
    assert result.stderr == (
        "error: prompts/implementer.md.j2: undefined variable 'nope' (line 1)\n"
    )


def test_missing_dependency_is_shown(workspace: Path) -> None:
    add_tickets(workspace)
    (workspace / "tickets" / "T02-daemon-and-cli-scaffold.md").unlink()
    result = runner.invoke(app, ["prompt", "show", "demo", "T04"])
    assert result.exit_code == 0, result.stderr
    assert "- T02 · (not found) (missing)" in result.stdout
