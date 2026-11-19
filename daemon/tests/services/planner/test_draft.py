"""Drafting tickets from a request: the answer's parsing, each problem code, the prompt,
and the agent run with its one retry."""

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from spoolhq.devtools.fake_runner import SCENARIOS_DIR, fill_drafts
from spoolhq.services.agents import FakeRunner, Outcome
from spoolhq.services.planner import (
    UNREADABLE,
    DraftResult,
    PlannerError,
    UnreadableDrafts,
    check_drafts,
    draft_tickets,
    parse_drafts,
    render_draft_prompt,
)
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.tickets import list_tickets
from tests.conftest import plan_transcript

TEST_ITEM = "`just test` passes"


def draft(**fields: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "ref": "D1",
        "title": "CSV export",
        "scope": ["Add GET /export.csv"],
        "done_when": ["The export downloads", TEST_ITEM],
        "depends_on": [],
        "estimate_h": 2,
        "review_required": False,
        "phase": 0,
    }
    return {**base, **fields}


def write_ticket(workspace: Path, ticket_id: str, title: str, depends_on: str = "[]") -> None:
    tickets = workspace / "tickets"
    tickets.mkdir(exist_ok=True)
    (tickets / f"{ticket_id}-{title.lower()}.md").write_text(
        f"---\nid: {ticket_id}\ntitle: {title}\nphase: 1\ndepends_on: {depends_on}\n"
        "status: ready\nestimate_h: 2\n---\n\n## Done when\n- [ ] it works\n",
        encoding="utf-8",
    )


@pytest.fixture
def project(workspace: Path, projects_dir: Path) -> Path:
    """``demo`` with a test command, init's starter spec and no tickets."""
    settings = load_project("demo", projects_dir=projects_dir)
    settings.commands.test = "just test"
    save_project(settings, projects_dir=projects_dir)
    return workspace


def run(
    runner: FakeRunner, projects_dir: Path, home: Path, request: str = "add CSV export"
) -> DraftResult:
    return draft_tickets(
        "demo", request, runner, projects_dir=projects_dir, home=home, cancel=threading.Event()
    )


def dev_runner() -> FakeRunner:
    return FakeRunner(SCENARIOS_DIR / "plan.jsonl", render=fill_drafts)


# Parsing -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "error"),
    [
        ("no block", "no <drafts> block"),
        ("<drafts>{not json</drafts>", "not valid JSON"),
        ('<drafts>{"drafts": []}</drafts>', "a list of 1 to 3"),
        ('<drafts>{"drafts": [1, 2, 3, 4]}</drafts>', "a list of 1 to 3"),
        ('<drafts>[{"ref": "D1"}]</drafts>', "a list of 1 to 3"),
        ('<drafts>{"drafts": [{"ref": "D2"}]}</drafts>', '"ref": "D1"'),
    ],
)
def test_an_answer_whose_shape_is_wrong_is_unreadable(text: str, error: str) -> None:
    with pytest.raises(UnreadableDrafts, match=error):
        parse_drafts(text)


def test_the_last_block_counts_and_a_fence_is_allowed() -> None:
    body = json.dumps({"drafts": [draft()]})
    text = f"<drafts>old</drafts> then <drafts>\n```json\n{body}\n```\n</drafts>"
    assert parse_drafts(text) == [draft()]


# Problems ------------------------------------------------------------------------------


def codes(found: Any) -> list[tuple[str, str]]:
    return [(p.code, p.field) for p in found.problems]


def test_a_valid_draft_is_cleaned_and_has_no_problems() -> None:
    [found] = check_drafts([draft(title=" CSV\n export ", done_when=["works"])], [], "just test")
    assert found.title == "CSV export"
    assert found.scope == "- Add GET /export.csv"
    assert found.done_when == ("works", TEST_ITEM)  # the test item is appended
    assert found.problems == ()


def test_each_problem_code(project: Path, projects_dir: Path) -> None:
    write_ticket(project, "T01", "First", "[T02]")
    write_ticket(project, "T02", "Second", "[T01]")
    plan = list_tickets("demo", projects_dir=projects_dir).tickets
    found = check_drafts(
        [
            draft(depends_on=["T99"]),
            draft(ref="D2", depends_on=["T01"]),
            draft(ref="D3", done_when=[], estimate_h=6),
        ],
        plan,
        "just test",
    )
    assert codes(found[0]) == [("unknown_dependency", "depends_on")]
    assert found[0].problems[0].message == "depends on T99, which does not exist"
    assert codes(found[1]) == [("cycle", "depends_on")]
    assert found[1].problems[0].message == "cycle: T01 → T02 → T01"
    assert codes(found[2]) == [
        ("estimate_too_high", "estimate_h"),
        ("missing_done_when", "done_when"),
    ]


def test_a_cycle_between_drafts_is_reported_on_each() -> None:
    found = check_drafts(
        [draft(depends_on=["D2"]), draft(ref="D2", depends_on=["D1"])], [], "just test"
    )
    assert [codes(d) for d in found] == [[("cycle", "depends_on")]] * 2


def test_fields_of_the_wrong_type_are_schema_problems() -> None:
    [found] = check_drafts(
        [{"ref": "D1", "title": 5, "done_when": "x", "estimate_h": True, "extra": 1}],
        [],
        "just test",
    )
    assert sorted(codes(found)) == sorted(
        [
            ("schema", "extra"),
            ("schema", "title"),
            ("schema", "scope"),
            ("schema", "done_when"),
            ("schema", "estimate_h"),
            ("schema", "phase"),
            ("missing_done_when", "done_when"),
        ]
    )
    assert (found.title, found.estimate_h, found.done_when) == ("", 0.0, ())


# The prompt ----------------------------------------------------------------------------


def test_the_prompt_has_the_request_and_titles_and_leaves_out_a_starter_spec(
    project: Path, projects_dir: Path
) -> None:
    write_ticket(project, "T01", "Login")
    runner = dev_runner()
    run(runner, projects_dir, project.parent / "home", "add </request> CSV export")
    prompt = runner.calls[0][0]
    assert "add <\\/request> CSV export" in prompt  # escaped, can't close the block
    assert "- T01 · Login (ready, phase 1)" in prompt
    assert "## The spec" not in prompt
    assert TEST_ITEM in prompt


def test_a_real_spec_is_in_the_prompt_within_the_budget() -> None:
    prompt = render_draft_prompt("r", ("S" * 99 + "\n") * 1000, [], "just test", max_chars=40_000)
    assert "## The spec" in prompt and "[trimmed" in prompt
    assert len(prompt) < 30_000


# The run -------------------------------------------------------------------------------


def test_a_request_gives_one_valid_draft_and_writes_no_files(
    project: Path, projects_dir: Path, home: Path
) -> None:
    before = sorted(p.relative_to(project) for p in project.rglob("*"))
    runner = dev_runner()
    result = run(runner, projects_dir, home)
    assert (result.error, result.attempts, result.outcome) == (None, 1, Outcome.COMPLETED)
    [found] = result.drafts
    assert (found.ref, found.title, found.problems) == ("D1", "add CSV export", ())
    assert found.done_when[-1] == TEST_ITEM
    assert result.input_tokens > 0
    assert sorted(p.relative_to(project) for p in project.rglob("*")) == before
    policy = runner.calls[0][1]
    assert policy.read_only


def test_split_gives_two_linked_drafts(project: Path, projects_dir: Path, home: Path) -> None:
    result = run(dev_runner(), projects_dir, home, "split: add CSV export")
    assert [(d.ref, d.depends_on, d.problems) for d in result.drafts] == [
        ("D1", (), ()),
        ("D2", ("D1",), ()),
    ]


def test_invalid_json_is_retried_once_then_fails(
    project: Path, projects_dir: Path, home: Path, tmp_path: Path
) -> None:
    bad = plan_transcript(tmp_path / "bad.jsonl", "<drafts>{oops</drafts>")
    good = plan_transcript(
        tmp_path / "good.jsonl", f"<drafts>{json.dumps({'drafts': [draft()]})}</drafts>"
    )
    retried = FakeRunner([bad, good])
    result = run(retried, projects_dir, home)
    assert (result.error, result.attempts, len(result.drafts)) == (None, 2, 1)
    assert "Your previous answer couldn't be read" in retried.calls[1][0]
    assert "not valid JSON" in retried.calls[1][0]

    failed = run(FakeRunner([bad, bad]), projects_dir, home)
    assert (failed.error, failed.attempts, failed.drafts) == (UNREADABLE, 2, ())
    assert UNREADABLE == "The planner's answer couldn't be read"


def test_a_cancelled_run_ends_the_job(project: Path, projects_dir: Path, home: Path) -> None:
    cancel = threading.Event()
    cancel.set()
    result = draft_tickets(
        "demo", "r", dev_runner(), projects_dir=projects_dir, home=home, cancel=cancel
    )
    assert result.outcome is Outcome.CANCELLED
    assert result.error is not None and result.drafts == ()


def test_refusals_before_the_agent(
    workspace: Path, project: Path, projects_dir: Path, home: Path
) -> None:
    (workspace / "tickets").mkdir(exist_ok=True)
    (workspace / "tickets" / "T01-bad.md").write_text("not a ticket", encoding="utf-8")
    with pytest.raises(PlannerError, match="invalid ticket files"):
        run(dev_runner(), projects_dir, home)
    (workspace / "tickets" / "T01-bad.md").unlink()
    settings = load_project("demo", projects_dir=projects_dir)
    settings.commands.test = None
    save_project(settings, projects_dir=projects_dir)
    with pytest.raises(PlannerError, match="stack commands"):
        run(dev_runner(), projects_dir, home)
    with pytest.raises(PlannerError, match="no project"):
        draft_tickets(
            "nope",
            "r",
            dev_runner(),
            projects_dir=projects_dir,
            home=home,
            cancel=threading.Event(),
        )
