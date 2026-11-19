import json
import shutil
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from spoolhq.api import create_app
from spoolhq.cli import app
from spoolhq.cli import tickets as tickets_cli
from spoolhq.cli.client import ApiClient
from spoolhq.core.config import load_settings
from spoolhq.devtools.fake_runner import SCENARIOS_DIR, fill_drafts
from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents
from spoolhq.services.tickets import load_ticket
from tests.conftest import AGENT_FIXTURES, FIXTURES_DIR, REVIEW_FIXTURES, plan_transcript

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


def test_new_writes_the_same_file_as_the_api(
    workspace: Path, projects_dir: Path, client: TestClient, token: str
) -> None:
    scope = "- Parse the thing.\n- Keep it small.\n"
    result = runner.invoke(
        app,
        ["tickets", "new", "demo", "--title", "Parse; it", "--done-when", "It parses",
         "--done-when", "`just test` passes", "--estimate", "2", "--phase", "4",
         "--review-required"],
        input=scope,
    )  # fmt: skip
    assert result.exit_code == 0, result.stderr
    assert result.stdout == "Added T01 (ready): tickets/T01-parse-it.md\n"
    from_cli = workspace / "tickets" / "T01-parse-it.md"
    answer = client.post(
        "/api/projects/demo/tickets",
        json={
            "title": "Parse; it",
            "scope": scope,
            "done_when": "- [ ] It parses\n- [ ] `just test` passes",
            "estimate_h": 2,
            "phase": 4,
            "review_required": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert answer.status_code == 201, answer.json()
    from_api = (workspace / "tickets" / "T02-parse-it.md").read_text(encoding="utf-8")
    expected = from_cli.read_text(encoding="utf-8").replace("id: T01", "id: T02")
    assert from_api == expected


def test_new_reads_the_scope_file_and_names_the_bad_field(workspace: Path, tmp_path: Path) -> None:
    scope = tmp_path / "scope.md"
    scope.write_text("From a file.\n", encoding="utf-8")
    args = ["tickets", "new", "demo", "--title", "T", "--done-when", "ok", "--scope-file"]
    assert runner.invoke(app, [*args, str(scope)]).exit_code == 0
    text = (workspace / "tickets" / "T01-t.md").read_text(encoding="utf-8")
    assert "From a file.\n\n## Done when\n- [ ] ok\n" in text
    bad = runner.invoke(app, [*args, str(scope), "--depends-on", "T50,T51"])
    assert bad.exit_code == 1
    assert "depends_on: depends on T50, T51, which does not exist" in bad.stderr
    blank = runner.invoke(app, ["tickets", "new", "demo", "--title", " ", "--done-when", "ok"])
    assert (blank.exit_code, "title" in blank.stderr) == (1, True)
    assert len(list((workspace / "tickets").iterdir())) == 1


# spool tickets draft -------------------------------------------------------------------


def draft_daemon(
    token: str, monkeypatch: pytest.MonkeyPatch, planner: FakeRunner | None = None
) -> TestClient:
    """The app with ``planner`` (default: the dev fake's drafts); `spool tickets draft`
    talks to it, polling fast."""
    settings = load_settings()
    agents = Agents(
        implementer=FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl"),
        reviewer=FakeRunner(REVIEW_FIXTURES / "approve.jsonl"),
        planner=planner or FakeRunner(SCENARIOS_DIR / "plan.jsonl", render=fill_drafts),
    )
    client = TestClient(
        create_app(settings, token=token, agents=agents),
        base_url=f"http://127.0.0.1:{settings.port}",
    )

    def forward(request: httpx.Request) -> httpx.Response:
        response = client.request(
            request.method, request.url.path, content=request.content, headers=request.headers
        )
        return httpx.Response(
            response.status_code, headers=response.headers, content=response.content
        )

    monkeypatch.setattr(
        tickets_cli,
        "_client",
        lambda: ApiClient("http://127.0.0.1:8765", token, transport=httpx.MockTransport(forward)),
    )
    monkeypatch.setattr(tickets_cli, "POLL_S", 0.02)
    return client


def ticket_files(workspace: Path) -> list[str]:
    return sorted(path.name for path in (workspace / "tickets").iterdir())


def test_draft_prints_the_drafts(
    run_project: Path, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    with draft_daemon(token, monkeypatch):
        result = runner.invoke(app, ["tickets", "draft", "demo", "split: add CSV export"])
    assert result.exit_code == 0, result.output
    assert "## D1 · split: add CSV export (part 1)" in result.output
    assert "## D2 · split: add CSV export (part 2)" in result.output
    assert "Phase 0 · 2.5h · review: no · depends on: D1" in result.output
    assert "- [ ] The change works as the request asks" in result.output
    assert ticket_files(run_project) == ["T07-parse-slug.md"]


def test_draft_save_writes_them(
    run_project: Path, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    with draft_daemon(token, monkeypatch):
        result = runner.invoke(
            app, ["tickets", "draft", "demo", "--save"], input="split: add CSV export\n"
        )
    assert result.exit_code == 0, result.output
    assert "Added T08 (ready): tickets/T08-split-add-csv-export-part-1.md" in result.output
    assert "Added T09 (ready): tickets/T09-split-add-csv-export-part-2.md" in result.output
    saved = load_ticket("demo", "T09", projects_dir=run_project.parent)
    assert saved.meta.depends_on == ["T08"]


def test_draft_save_refuses_drafts_with_problems(
    run_project: Path, token: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    answer = {
        "drafts": [
            {
                "ref": "D1",
                "title": "x",
                "scope": ["y"],
                "done_when": ["z"],
                "depends_on": ["T99"],
                "estimate_h": 6,
                "phase": 0,
            }
        ]
    }
    text = f"<drafts>{json.dumps(answer)}</drafts>"
    planner = FakeRunner(plan_transcript(tmp_path / "answer.jsonl", text))
    with draft_daemon(token, monkeypatch, planner):
        result = runner.invoke(app, ["tickets", "draft", "demo", "r", "--save"])
    assert result.exit_code == 1
    assert "- depends_on: depends on T99, which does not exist" in result.output
    assert "- estimate_h: 6 h is over 4 h: split the work" in result.output
    assert "not saved: fix the problems above" in result.output
    assert ticket_files(run_project) == ["T07-parse-slug.md"]


def test_draft_reports_a_failed_job_and_a_refusal(
    run_project: Path, token: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    bad = plan_transcript(tmp_path / "bad.jsonl", "no drafts here")
    with draft_daemon(token, monkeypatch, FakeRunner([bad, bad])):
        failed = runner.invoke(app, ["tickets", "draft", "demo", "r"])
        refused = runner.invoke(app, ["tickets", "draft", "nope", "r"])
    assert failed.exit_code == 1
    assert "error: The planner's answer couldn't be read" in failed.output
    assert refused.exit_code == 1
    assert "no project 'nope'" in refused.output
