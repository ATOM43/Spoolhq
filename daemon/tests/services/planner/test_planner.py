import copy
import hashlib
import json
import threading
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import FakeRunner, Outcome
from spoolhq.services.planner import (
    PLAN_FILE,
    PLANNER_MAX_TURNS,
    PlannerError,
    PlanResult,
    approve_plan,
    generate_plan,
)
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.projects.model import Budget
from spoolhq.services.scheduler import validate_plan
from spoolhq.services.tickets import list_tickets
from tests.conftest import DASHBOARD_PLAN, REVIEW_FIXTURES, dashboard_plan, plan_transcript


def plan(runner: FakeRunner, projects_dir: Path, home: Path, **kwargs: Any) -> PlanResult:
    return generate_plan(
        "demo", runner, projects_dir=projects_dir, home=home, cancel=threading.Event(), **kwargs
    )


def snapshot(tickets: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(tickets.iterdir())}


def without(data: dict[str, Any], *ids: str) -> dict[str, Any]:
    return {"tickets": [t for t in data["tickets"] if t["id"] not in ids]}


def revised(data: dict[str, Any]) -> dict[str, Any]:
    """The same plan with every title changed, so replaced files are visibly new."""
    data = copy.deepcopy(data)
    for ticket in data["tickets"]:
        ticket["title"] += " (v2)"
    return data


# Done when 1: the dashboard spec gives a valid plan that approval makes ready ----------


def test_dashboard_plan_writes_18_valid_drafts_and_approval_makes_them_ready(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    runner = FakeRunner(DASHBOARD_PLAN)
    result = plan(runner, projects_dir, home)

    assert result.error is None, result.error
    assert result.outcome is Outcome.COMPLETED
    assert result.written == tuple(f"T{n:02d}" for n in range(1, 19))
    assert (result.attempts, result.deleted, result.kept) == (1, (), ())
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert listing.invalid == []
    assert validate_plan(listing.tickets) == []
    assert len(listing.tickets) == 18
    expected = {t["id"]: t for t in dashboard_plan()["tickets"]}
    for ticket in listing.tickets:
        assert ticket.meta.status == "draft"
        assert ticket.done_when, ticket.id
        assert ticket.done_when[-1].text == "`just test` passes"
        assert ticket.meta.title == expected[ticket.id]["title"]
        assert ticket.meta.depends_on == expected[ticket.id]["depends_on"]
        assert ticket.meta.estimate_h == expected[ticket.id]["estimate_h"]
        assert "## Purpose" in ticket.body and "## Scope" in ticket.body
    assert listing.tickets[3].meta.review_required  # T04: migrations

    # The planner is read-only, in the project's repository, with 30 turns.
    [(prompt, policy)] = runner.calls
    assert policy.read_only
    assert policy.worktree == load_project("demo", projects_dir=projects_dir).repo_path
    assert "Simulation results dashboard" in prompt

    assert approve_plan("demo", projects_dir=projects_dir) == result.written
    statuses = {t.meta.status for t in list_tickets("demo", projects_dir=projects_dir).tickets}
    assert statuses == {"ready"}


def test_the_hashes_of_the_drafts_are_recorded(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)

    record = json.loads((plan_project / PLAN_FILE).read_text(encoding="utf-8"))
    assert set(record) == {"generated_at", "tickets"}
    files = {p.name[:3]: p for p in (plan_project / "tickets").iterdir()}
    assert record["tickets"] == {
        ticket_id: hashlib.sha256(path.read_bytes()).hexdigest()
        for ticket_id, path in files.items()
    }


# Done when 2: a draft the user edited survives a re-plan --------------------------------


def test_replan_keeps_an_edited_draft_and_replaces_the_rest(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)
    tickets = plan_project / "tickets"
    edited = tickets / "T05-assessment-logic.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nUse the 2026 rules.\n", "utf-8")
    edited_bytes = edited.read_bytes()

    # The new plan leaves out the kept T05 and drops T18.
    second = plan_transcript(
        tmp_path / "second.jsonl", revised(without(dashboard_plan(), "T05", "T18"))
    )
    runner = FakeRunner(second)
    result = plan(runner, projects_dir, home)

    assert result.error is None, result.error
    assert edited.read_bytes() == edited_bytes
    assert result.kept == ("T05",)
    assert result.deleted == ("T18",)
    assert "T05" not in result.written
    listing = list_tickets("demo", projects_dir=projects_dir)
    titles = {t.id: t.meta.title for t in listing.tickets}
    assert "T18" not in titles
    assert titles["T01"] == "Repository and tooling (v2)"
    assert titles["T05"] == "Assessment logic"
    assert sorted(p.name for p in tickets.iterdir() if p.name.startswith("T01")) == [
        "T01-repository-and-tooling-v2.md"  # the old file name is gone
    ]
    # The edited ticket went to the planner as fixed input.
    prompt = runner.calls[0][0]
    assert "<kept_tickets>" in prompt and "Use the 2026 rules." in prompt


def test_replan_keeps_a_hand_made_draft(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)
    tickets = plan_project / "tickets"
    hand = tickets / "T19-extra.md"
    hand.write_text(
        "---\nid: T19\ntitle: Extra\nphase: 4\ndepends_on: [T18]\nstatus: draft\n"
        "estimate_h: 2\n---\n\n## Done when\n- [ ] done\n",
        encoding="utf-8",
    )
    before = hand.read_bytes()

    result = plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)

    assert result.error is None, result.error
    assert result.kept == ("T19",)
    assert hand.read_bytes() == before


# 3: re-planning never touches tickets past draft; ids continue --------------------------


def test_replan_leaves_ready_and_done_tickets_and_continues_the_ids(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    tickets = plan_project / "tickets"
    for ticket_id, status in (("T01", "done"), ("T02", "ready")):
        deps = "[T01]" if ticket_id == "T02" else "[]"
        (tickets / f"{ticket_id}-x.md").write_text(
            f"---\nid: {ticket_id}\ntitle: Old {ticket_id}\nphase: 0\ndepends_on: {deps}\n"
            f"status: {status}\nestimate_h: 2\n---\n\n## Done when\n- [ ] ok\n",
            encoding="utf-8",
        )
    before = snapshot(tickets)
    new = {
        "tickets": [
            {
                "id": "T03",
                "title": "Next",
                "phase": 1,
                "purpose": "Continue.",
                "depends_on": ["T02"],
                "estimate_h": 2,
                "scope": ["more"],
                "done_when": ["it works"],
            }
        ]
    }
    runner = FakeRunner(plan_transcript(tmp_path / "next.jsonl", new))
    result = plan(runner, projects_dir, home)

    assert result.error is None, result.error
    assert result.written == ("T03",)
    assert result.kept == ("T01", "T02")
    after = snapshot(tickets)
    assert {name: after[name] for name in before} == before
    prompt = runner.calls[0][0]
    assert "New tickets take ids from T03 upward" in prompt


def test_new_ids_below_the_highest_existing_one_are_refused(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    tickets = plan_project / "tickets"
    (tickets / "T05-x.md").write_text(
        "---\nid: T05\ntitle: Done\nphase: 0\nstatus: done\nestimate_h: 2\n---\n",
        encoding="utf-8",
    )
    data = {"tickets": [dashboard_plan()["tickets"][0]]}  # T01, no dependencies
    bad = plan_transcript(tmp_path / "bad.jsonl", data)
    result = plan(FakeRunner([bad, bad]), projects_dir, home)

    assert result.error == "planner output invalid: T01: new ids continue from T06"


# 4: invalid output is retried once with the exact errors, then nothing is written ------


def _cycle() -> dict[str, Any]:
    data = dashboard_plan()
    data["tickets"][0]["depends_on"] = ["T18"]
    return data


def _estimate() -> dict[str, Any]:
    data = dashboard_plan()
    data["tickets"][6]["estimate_h"] = 6
    return data


def _duplicate() -> dict[str, Any]:
    data = dashboard_plan()
    data["tickets"][1]["id"] = "T01"
    return data


CYCLE = "cycle: T01 → T02 → T03 → T11 → T12 → T13 → T16 → T17 → T18 → T01"


@pytest.mark.parametrize(
    ("bad", "error"),
    [
        (_cycle(), CYCLE),
        (_estimate(), "T07: estimate_h: Input should be less than or equal to 4"),
        (_duplicate(), "T01: the id appears more than once"),
        (
            "<plan>{not json</plan>",
            "the <plan> block is not valid JSON: Expecting property name enclosed in double "
            "quotes: line 1 column 2 (char 1)",
        ),
    ],
    ids=["cycle", "estimate", "duplicate", "malformed"],
)
def test_invalid_output_is_retried_with_the_errors_then_fails(
    bad: dict[str, Any] | str,
    error: str,
    plan_project: Path,
    projects_dir: Path,
    home: Path,
    tmp_path: Path,
) -> None:
    first = plan_transcript(tmp_path / "first.jsonl", bad)
    second = plan_transcript(tmp_path / "second.jsonl", bad)
    runner = FakeRunner([first, second])
    result = plan(runner, projects_dir, home)

    assert result.attempts == 2
    assert result.error is not None
    assert result.error.startswith("planner output invalid: ")
    assert error in result.error
    retry = runner.calls[1][0]
    assert "## Your previous answer was invalid:" in retry
    assert f"- {error}\n" in retry
    assert "## Your previous answer was invalid:" not in runner.calls[0][0]
    assert list((plan_project / "tickets").iterdir()) == []
    assert not (plan_project / PLAN_FILE).exists()
    assert (result.input_tokens, result.output_tokens) == (2000, 500)


def test_a_valid_retry_writes_the_plan(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    first = plan_transcript(tmp_path / "first.jsonl", "no plan here")
    result = plan(FakeRunner([first, DASHBOARD_PLAN]), projects_dir, home)

    assert result.error is None
    assert result.attempts == 2
    assert len(result.written) == 18


# 5: a kept ticket depending on a dropped draft -----------------------------------------


def test_a_kept_ticket_depending_on_a_dropped_draft_fails_and_changes_nothing(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)
    tickets = plan_project / "tickets"
    edited = tickets / "T18-documentation-and-handover.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nAlso a video.\n", "utf-8")
    before = snapshot(tickets)
    record = (plan_project / PLAN_FILE).read_bytes()

    # The new plan leaves out T18 (kept, fine) and T17, which T18 depends on.
    drop = plan_transcript(tmp_path / "drop.jsonl", without(dashboard_plan(), "T17", "T18"))
    result = plan(FakeRunner([drop, drop]), projects_dir, home)

    assert result.error == (
        "planner output invalid: T18 is kept and depends on T17, which the new plan drops"
    )
    assert snapshot(tickets) == before
    assert (plan_project / PLAN_FILE).read_bytes() == record


# Runs that don't complete, the budget, the inputs ----------------------------------------


def test_a_run_that_does_not_complete_writes_nothing(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    result = plan(FakeRunner(REVIEW_FIXTURES / "usage_limited.jsonl"), projects_dir, home)

    assert result.outcome is Outcome.USAGE_LIMITED
    assert result.error is not None and result.error.startswith("planner run ended: usage_limited")
    assert result.attempts == 1
    assert list((plan_project / "tickets").iterdir()) == []


def test_the_token_budget_limits_the_planner(
    plan_project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    project = load_project("demo", projects_dir=projects_dir)
    project.agents.budget_per_ticket = Budget(tokens=1250)
    save_project(project, projects_dir=projects_dir)
    first = plan_transcript(tmp_path / "first.jsonl", "no plan", tokens=1000)
    runner = FakeRunner([first, first])

    result = plan(runner, projects_dir, home)

    # 1,000 in + 250 out = 1,250 weighted: the cap is used up, so no second attempt.
    assert result.error == "budget used up: 1,250 of 1,250 weighted tokens"
    assert len(runner.calls) == 1


def test_the_budget_and_turns_reach_the_runner(
    plan_project: Path, projects_dir: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = load_project("demo", projects_dir=projects_dir)
    project.agents.budget_per_ticket = Budget(tokens=50_000)
    save_project(project, projects_dir=projects_dir)
    runner = FakeRunner(DASHBOARD_PLAN)
    budgets = []
    original = runner.run

    def spy(prompt: str, policy: Any, budget: Any, **kwargs: Any) -> Any:
        budgets.append(budget)
        return original(prompt, policy, budget, **kwargs)

    monkeypatch.setattr(runner, "run", spy)
    plan(runner, projects_dir, home)

    assert (budgets[0].max_turns, budgets[0].max_tokens) == (PLANNER_MAX_TURNS, 50_000)


def test_the_template_description_reaches_the_prompt(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    runner = FakeRunner(DASHBOARD_PLAN)
    plan(runner, projects_dir, home, template_description="FastAPI + React, with CI.")

    prompt = runner.calls[0][0]
    assert "<template>" in prompt and "FastAPI + React, with CI." in prompt
    assert "Its setup counts as done" in prompt


def test_the_stored_template_description_is_used_by_default(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    (plan_project / "TEMPLATE.md").write_text("Stored: FastAPI + React.", encoding="utf-8")
    runner = FakeRunner([DASHBOARD_PLAN, DASHBOARD_PLAN])
    plan(runner, projects_dir, home)
    prompt = runner.calls[0][0]
    assert "<template>" in prompt and "Stored: FastAPI + React." in prompt
    assert "Its setup counts as done" in prompt

    plan(runner, projects_dir, home, template_description="Given instead.")
    assert "Given instead." in runner.calls[1][0]
    assert "Stored: FastAPI + React." not in runner.calls[1][0]


def test_no_template_means_no_template_rule(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    runner = FakeRunner(DASHBOARD_PLAN)
    plan(runner, projects_dir, home)
    assert "Its setup counts as done" not in runner.calls[0][0]


def test_a_missing_spec_is_refused(workspace: Path, projects_dir: Path, home: Path) -> None:
    (workspace / "CONTEXT.md").unlink()
    with pytest.raises(PlannerError, match="no CONTEXT.md in .*: write the spec there first"):
        plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)


def test_invalid_ticket_files_are_refused(
    plan_project: Path, projects_dir: Path, home: Path
) -> None:
    (plan_project / "tickets" / "T01-x.md").write_text("no frontmatter\n", encoding="utf-8")
    with pytest.raises(PlannerError, match="some ticket files are invalid; fix them first"):
        plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)


def test_an_unknown_project_is_refused(projects_dir: Path, home: Path) -> None:
    projects_dir.mkdir()
    with pytest.raises(PlannerError):
        plan(FakeRunner(DASHBOARD_PLAN), projects_dir, home)
