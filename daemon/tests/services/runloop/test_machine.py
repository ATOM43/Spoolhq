"""The state machine end to end: fake runners, fake gates, a real git repo and run log."""

from pathlib import Path

import pytest

from spoolhq.services.agents import AgentPolicy, FakeRunner
from spoolhq.services.projects import Budget as ProjectBudget
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import HoldForIntegration, RunLoop, next_kind
from spoolhq.services.runs import (
    Attempt,
    AttemptKind,
    AttemptStatus,
    EventKind,
    Run,
    RunLog,
    RunRegistry,
    RunStatus,
)
from spoolhq.services.tickets import load_ticket
from tests.conftest import run_git
from tests.services.runloop.conftest import (
    PASSING,
    Hooked,
    LoopFactory,
    Merging,
    Transcripts,
    failing,
)


def run_once(loop: RunLoop, ticket: str | None = None) -> Run:
    run = loop.start("demo", "next", ticket)
    loop.wait("demo")
    return run


def log_of(registry: RunRegistry) -> RunLog:
    return registry.get("demo").run_log


def phases(log: RunLog, run_id: int) -> list[str]:
    return [
        str(event.payload["phase"])
        for event in log.events_since(0, run_id=run_id)
        if event.kind is EventKind.RUN_PHASE
    ]


def kinds(attempts: list[Attempt]) -> list[tuple[str, str]]:
    return [(attempt.kind.value, attempt.status.value) for attempt in attempts]


def ticket_status(projects_dir: Path, ticket_id: str = "T01") -> str:
    return load_ticket("demo", ticket_id, projects_dir=projects_dir).meta.status


def test_happy_path(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    merging = Merging()
    loop, gates = make_loop(
        [transcripts.implement({"hello.py": "def hello():\n    return 'hi'\n"})],
        [transcripts.review("approve")],
        integrator=merging,
    )

    run = run_once(loop)

    log = log_of(registry)
    final = log.get_run(run.id)
    assert final.status is RunStatus.DONE
    assert final.progress_note == "Added hello."
    assert ticket_status(projects_dir) == "done"
    assert kinds(log.list_attempts(run.id)) == [("initial", "approved")]
    assert merging.commits == {"T01": ["spool: T01 attempt 1"]}
    assert phases(log, run.id) == [
        "picked",
        "worktree",
        "implement",
        "commit",
        "gates",
        "review",
        "integrate",
        "done",
    ]
    assert gates.calls == [worktrees / "demo" / "T01"]
    assert not (worktrees / "demo" / "T01").exists()
    attempt = log.list_attempts(run.id)[0]
    folder = log.workspace / attempt.dir
    assert {"transcript.jsonl", "gates.json", "diff.patch", "review.json"} <= {
        path.name for path in folder.iterdir()
    }
    assert "+def hello():" in (folder / "diff.patch").read_text(encoding="utf-8")
    usage = log.run_usage(run.id)
    assert usage.total_tokens == 1250 + 625


def test_gate_retry_feeds_the_failing_tests_into_the_next_prompt(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop(
        [transcripts.implement(), transcripts.implement({"hello.py": "x = 2\n"})],
        [transcripts.review("approve")],
        gates=[failing("tests/test_hello.py::test_one", "tests/test_hello.py::test_two"), PASSING],
    )

    run = run_once(loop)

    log = log_of(registry)
    assert log.get_run(run.id).status is RunStatus.DONE
    assert kinds(log.list_attempts(run.id)) == [
        ("initial", "gates_failed"),
        ("gate_retry", "approved"),
    ]
    retry_prompt = loop.agents.implementer.calls[1][0]  # type: ignore[attr-defined]
    assert "The checks failed on your last attempt (attempt 1)" in retry_prompt
    assert "`tests/test_hello.py::test_one`" in retry_prompt
    assert "`tests/test_hello.py::test_two`" in retry_prompt
    assert "Previous attempt" not in loop.agents.implementer.calls[0][0]  # type: ignore[attr-defined]


def test_review_retry_feeds_the_unmet_item_into_the_next_prompt(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop(
        [transcripts.implement(), transcripts.implement()],
        [
            transcripts.review(
                "changes_requested",
                (True, False, True),
                ("hello exists", "no test calls hello()", "gates"),
            ),
            transcripts.review("approve"),
        ],
    )

    run = run_once(loop)

    log = log_of(registry)
    assert log.get_run(run.id).status is RunStatus.DONE
    assert kinds(log.list_attempts(run.id)) == [
        ("initial", "changes_requested"),
        ("review_retry", "approved"),
    ]
    retry_prompt = loop.agents.implementer.calls[1][0]  # type: ignore[attr-defined]
    assert "The reviewer asked for changes (attempt 1)" in retry_prompt
    assert "- not met: A test covers hello — no test calls hello()" in retry_prompt
    assert "hello exists" not in retry_prompt  # only the unmet items


def test_gates_failing_four_times_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    loop, gates = make_loop(
        [transcripts.implement() for _ in range(4)], gates=[failing("tests/t.py::test_a")]
    )

    run = run_once(loop)

    log = log_of(registry)
    final = log.get_run(run.id)
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "gates failed after 3 retries: just test",
    )
    assert [a.kind for a in log.list_attempts(run.id)] == [
        AttemptKind.INITIAL,
        *[AttemptKind.GATE_RETRY] * 3,
    ]
    assert len(gates.calls) == 4
    assert ticket_status(projects_dir) == "blocked"
    assert (worktrees / "demo" / "T01" / "hello.py").is_file()


def test_changes_requested_three_times_blocks(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, worktrees: Path
) -> None:
    unmet = (True, False, True)
    loop, _ = make_loop(
        [transcripts.implement() for _ in range(3)],
        [transcripts.review("changes_requested", unmet) for _ in range(3)],
    )

    run = run_once(loop)

    final = log_of(registry).get_run(run.id)
    assert (final.status, final.reason) == (RunStatus.BLOCKED, "changes requested after 2 retries")
    assert (worktrees / "demo" / "T01").is_dir()


def test_needs_human_blocks_at_once(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, worktrees: Path
) -> None:
    loop, _ = make_loop([transcripts.implement()], [transcripts.review("needs_human")])

    run = run_once(loop)

    final = log_of(registry).get_run(run.id)
    assert final.status is RunStatus.BLOCKED
    assert final.reason == "the reviewer asked for a person: needs_human."
    assert len(log_of(registry).list_attempts(run.id)) == 1
    assert (worktrees / "demo" / "T01").is_dir()


def test_policy_violation_blocks_without_a_retry(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, worktrees: Path
) -> None:
    loop, gates = make_loop([transcripts.implement(outcome="policy_violation")])

    run = run_once(loop)

    log = log_of(registry)
    final = log.get_run(run.id)
    assert final.status is RunStatus.BLOCKED
    assert final.reason is not None
    assert final.reason.startswith("implementer error: policy not enforced: ")
    assert kinds(log.list_attempts(run.id)) == [("initial", "error")]
    assert len(loop.agents.implementer.calls) == 1  # type: ignore[attr-defined]
    assert gates.calls == []
    assert (worktrees / "demo" / "T01").is_dir()


def test_agent_error_blocks_with_its_text(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop([transcripts.implement(outcome="error")])

    run = run_once(loop)

    reason = log_of(registry).get_run(run.id).reason
    assert reason is not None and "API Error: 500" in reason


def test_max_turns_uses_a_gate_retry_and_keeps_the_work(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop(
        [transcripts.implement(outcome="max_turns"), transcripts.implement()],
        [transcripts.review("approve")],
    )

    run = run_once(loop)

    log = log_of(registry)
    assert log.get_run(run.id).status is RunStatus.DONE
    assert kinds(log.list_attempts(run.id)) == [("initial", "error"), ("gate_retry", "approved")]
    retry_prompt = loop.agents.implementer.calls[1][0]  # type: ignore[attr-defined]
    assert (
        "Note from SpoolHQ:\n\nYour last attempt stopped before the checks ran (max_turns)"
        in retry_prompt
    )
    assert "Note from the user" not in retry_prompt


def test_budget_used_up_blocks_before_the_next_attempt(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    settings.agents.budget_per_ticket = ProjectBudget(tokens=2000)
    save_project(settings, projects_dir=projects_dir)
    loop, _ = make_loop(
        [transcripts.implement(), transcripts.implement(), transcripts.implement()],
        gates=[failing("tests/t.py::test_a")],
    )

    run = run_once(loop)

    log = log_of(registry)
    final = log.get_run(run.id)
    # Attempt 1 used 1,250 tokens; attempt 2 got the 750 left and stopped at 1,250.
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "budget used up: 2,500 of 2,000 tokens",
    )
    assert len(log.list_attempts(run.id)) == 2


def test_reviewer_that_changes_the_worktree_blocks(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    def write_file(policy: AgentPolicy) -> None:
        (policy.worktree / "sneaky.txt").write_text("x", encoding="utf-8")

    reviewer = Hooked(FakeRunner([transcripts.review("approve")]), write_file)
    loop, _ = make_loop([transcripts.implement()], reviewer)

    run = run_once(loop)

    final = log_of(registry).get_run(run.id)
    assert (final.status, final.reason) == (RunStatus.BLOCKED, "reviewer changed the worktree")


def test_default_integrator_holds_the_approved_ticket(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=HoldForIntegration()
    )

    run = loop.start("demo", "all")
    loop.wait("demo")

    log = log_of(registry)
    final = log.get_run(run.id)
    path = worktrees / "demo" / "T01"
    assert final.status is RunStatus.AWAITING_APPROVAL
    assert final.reason == (
        f"T01 approved; merge it with `spool run integrate demo T01` — worktree kept at {path}"
    )
    assert ticket_status(projects_dir) == "awaiting_approval"
    assert ticket_status(projects_dir, "T02") == "ready"  # run all stopped there
    assert path.is_dir()
    assert len(log.list_runs()) == 1


def test_run_all_runs_every_ready_ticket_in_id_order(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, projects_dir: Path
) -> None:
    merging = Merging()
    loop, _ = make_loop(
        [transcripts.implement() for _ in range(3)],
        [transcripts.review("approve") for _ in range(3)],
        integrator=merging,
    )

    loop.start("demo", "all")
    loop.wait("demo")

    assert merging.calls == ["T01", "T02", "T03"]
    assert [ticket_status(projects_dir, t) for t in ("T01", "T02", "T03")] == ["done"] * 3
    assert [run.status for run in log_of(registry).list_runs()] == [RunStatus.DONE] * 3


def test_run_all_stops_at_a_blocked_ticket(
    make_loop: LoopFactory, transcripts: Transcripts, projects_dir: Path
) -> None:
    loop, _ = make_loop(
        [transcripts.implement() for _ in range(2)],
        [transcripts.review("approve"), transcripts.review("needs_human")],
    )

    loop.start("demo", "all")
    loop.wait("demo")

    assert [ticket_status(projects_dir, t) for t in ("T01", "T02", "T03")] == [
        "done",
        "blocked",
        "ready",
    ]


def test_run_commits_on_the_branch_and_main_is_untouched(
    make_loop: LoopFactory, transcripts: Transcripts, repo: Path
) -> None:
    loop, _ = make_loop([transcripts.implement()], [transcripts.review("needs_human")])

    run_once(loop)

    branch = run_git(repo, "branch", "--list", "feat/T01-*", "--format=%(refname:short)").strip()
    assert run_git(repo, "log", "--format=%s", f"main..{branch}").splitlines() == [
        "spool: T01 attempt 1"
    ]
    assert run_git(repo, "log", "--format=%s", "main").splitlines() == ["initial commit"]


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        ([], AttemptKind.INITIAL),
        ([(AttemptKind.INITIAL, AttemptStatus.INTERRUPTED)], AttemptKind.INITIAL),
        ([(AttemptKind.REVIEW_RETRY, AttemptStatus.INTERRUPTED)], AttemptKind.REVIEW_RETRY),
        ([(AttemptKind.INITIAL, AttemptStatus.GATES_FAILED)], AttemptKind.GATE_RETRY),
        ([(AttemptKind.INITIAL, AttemptStatus.CHANGES_REQUESTED)], AttemptKind.REVIEW_RETRY),
        ([(AttemptKind.INITIAL, AttemptStatus.ERROR)], AttemptKind.GATE_RETRY),
        ([(AttemptKind.INITIAL, AttemptStatus.APPROVED)], None),
    ],
)
def test_next_kind(
    statuses: list[tuple[AttemptKind, AttemptStatus]], expected: AttemptKind | None
) -> None:
    attempts = [
        Attempt(
            i, 1, "T01", i, kind, status, "runs/T01/001", None, None, 0, 0, None, "", None, Path()
        )
        for i, (kind, status) in enumerate(statuses, start=1)
    ]
    assert next_kind(attempts) == expected
