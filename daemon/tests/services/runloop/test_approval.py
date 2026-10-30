"""The merge policy in the run loop (``approval.py``): each rule alone sends a ticket to
a pull request (fake GitHub, local bare remote) or, without a remote, to local
approval; approve and reject; runs that block never reach the policy."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli.main import app
from spoolhq.services.agents import FakeRunner
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import Delivery, RunLoopError
from spoolhq.services.runloop.pr_body import md_escape
from spoolhq.services.runs import AttemptKind, EventKind, Run, RunLog, RunRegistry, RunStatus
from spoolhq.services.tickets import load_ticket, save_ticket
from tests.conftest import GITHUB_URL, make_github_remote, run_git
from tests.services.runloop.conftest import (
    LoopFactory,
    ManualClock,
    Transcripts,
    failing,
)
from tests.services.runloop.test_pull_requests import FakeGitHub

TOKEN = "ghp_fake0123456789abcdefTOKEN"  # noqa: S105 - a fake token
CASES = ["review_required", "diff_size", "protected_paths", "needs_human"]
DETAILS = {
    "review_required": "the ticket is marked review_required",
    "diff_size": "401 lines > 400",
    "protected_paths": ".github/workflows/ci.yml",
    "needs_human": "needs_human.",
}
cli = CliRunner()


def log_of(registry: RunRegistry) -> RunLog:
    return registry.get("demo").run_log


def ticket_status(projects_dir: Path, ticket_id: str = "T01") -> str:
    return load_ticket("demo", ticket_id, projects_dir=projects_dir).meta.status


def decisions(log: RunLog, run: Run) -> list[dict[str, object]]:
    events = log.events_since(0, run_id=run.id, limit=10_000)
    return [e.payload for e in events if e.kind is EventKind.POLICY_DECISION]


@pytest.fixture
def remote(
    request: pytest.FixtureRequest,
    repo: Path,
    project: Path,
    projects_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> FakeGitHub | None:
    """``git.remote`` and a fake GitHub when the test is parametrised with True."""
    if not request.param:
        return None
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = GITHUB_URL
    save_project(settings, projects_dir=projects_dir)
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", TOKEN)
    return FakeGitHub(make_github_remote(repo, tmp_path / "remote.git"))


def run_case(
    case: str | None,
    make_loop: LoopFactory,
    transcripts: Transcripts,
    remote: FakeGitHub | None,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
) -> Run:
    """Run T01 changed in exactly one way from a ticket that would go direct."""
    files = {"hello.py": "x = 1\n"}
    if case == "review_required":
        ticket = load_ticket("demo", "T01", projects_dir=projects_dir)
        ticket.meta.review_required = True
        save_ticket("demo", ticket, projects_dir=projects_dir)
    elif case == "diff_size":
        files = {"hello.py": "x = 1\n" * 401}
    elif case == "direct-400":
        files = {"hello.py": "x = 1\n" * 400}
    elif case == "protected_paths":
        files = {".github/workflows/ci.yml": "on: push\n"}
    verdict = "needs_human" if case == "needs_human" else "approve"
    github = remote.client if remote is not None else None
    integrator = Delivery(clock=clock, github=github) if github else Delivery(clock=clock)
    loop, _ = make_loop(
        [transcripts.implement(files)], [transcripts.review(verdict)], integrator=integrator
    )
    loop.start("demo", "next")
    loop.wait("demo")
    return log_of(registry).list_runs()[0]


@pytest.mark.integration
@pytest.mark.parametrize("remote", [True, False], ids=["github", "local"], indirect=True)
@pytest.mark.parametrize("case", CASES)
def test_each_rule_alone_needs_a_person(
    case: str,
    remote: FakeGitHub | None,
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
) -> None:
    run = run_case(case, make_loop, transcripts, remote, clock, projects_dir, registry)

    detail = DETAILS[case]
    rules = [{"rule": case, "detail": detail}]
    assert run.status is RunStatus.AWAITING_APPROVAL
    assert ticket_status(projects_dir) == "awaiting_approval"
    if remote is not None:
        assert run.pr_number == 1
        assert run.policy == {"mode": "pr", "rules": rules}
        body = remote.pulls[1]["data"]["body"]
        assert body.startswith(f"## Why this needs you\n\n- **{md_escape(case)}**: ")
        assert body.split("\n")[2].endswith(md_escape(detail))
    else:
        assert run.pr_number is None
        assert run.policy == {"mode": "approval", "rules": rules}
        assert run.reason is not None
        assert run.reason.startswith(f"T01 needs you: {case} ({detail}); approve with")
    # Done when 2: one decision event naming the rule, and `spool runs show` prints it.
    assert decisions(log_of(registry), run) == [run.policy]
    shown = cli.invoke(app, ["runs", "show", "demo", str(run.id)])
    mode = "pr" if remote is not None else "approval"
    assert f"policy:     {mode} · needs you: {case} ({detail})" in shown.output


@pytest.mark.integration
@pytest.mark.parametrize("remote", [True, False], ids=["github", "local"], indirect=True)
def test_a_400_line_change_goes_direct_and_logs_no_hits(
    remote: FakeGitHub | None,
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
    repo: Path,
) -> None:
    run = run_case("direct-400", make_loop, transcripts, remote, clock, projects_dir, registry)

    assert run.status is RunStatus.DONE
    assert run.policy == {"mode": "direct", "rules": []}
    assert decisions(log_of(registry), run) == [run.policy]
    assert ticket_status(projects_dir) == "done"
    if remote is not None:
        assert remote.pulls == {}
        assert run_git(remote.bare, "rev-parse", "main") == run_git(repo, "rev-parse", "main")
    shown = cli.invoke(app, ["runs", "show", "demo", str(run.id)])
    assert "policy:     direct · no rule holds" in shown.output


@pytest.mark.integration
def test_approve_integrates_and_reject_needs_a_note(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
    repo: Path,
) -> None:
    loop, _ = make_loop(
        [transcripts.implement()],
        [transcripts.review("needs_human")],
        integrator=Delivery(clock=clock),
    )
    loop.start("demo", "next")
    loop.wait("demo")
    with pytest.raises(RunLoopError, match="say what should change with --note"):
        loop.reject("demo", "T01", "  ")

    loop.approve("demo", "T01")
    loop.wait("demo")

    log = log_of(registry)
    run = log.list_runs()[0]
    assert run.status is RunStatus.DONE
    assert ticket_status(projects_dir) == "done"
    assert run_git(repo, "log", "-1", "--format=%s", "main").strip() == "T01: Say hello T01"
    first, second = decisions(log, run)
    assert first["mode"] == "approval"
    assert second == {
        "mode": "direct",
        "rules": [{"rule": "needs_human", "detail": "needs_human."}],
        "approved_by_user": True,
    }
    with pytest.raises(RunLoopError, match="T01 is done, not awaiting approval"):
        loop.approve("demo", "T01")


@pytest.mark.integration
def test_reject_starts_a_pr_changes_attempt_with_the_note(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
) -> None:
    implementer = FakeRunner([transcripts.implement(), transcripts.implement()])
    loop, _ = make_loop(
        implementer,
        [transcripts.review("needs_human"), transcripts.review("approve")],
        integrator=Delivery(clock=clock),
    )
    loop.start("demo", "next")
    loop.wait("demo")

    loop.reject("demo", "T01", "rename the endpoint")
    loop.wait("demo")

    log = log_of(registry)
    run = log.list_runs()[0]
    attempts = log.list_attempts(run.id)
    assert [a.kind for a in attempts] == [AttemptKind.INITIAL, AttemptKind.PR_CHANGES]
    prompt = implementer.calls[1][0]
    assert "Note from the user:\n\nrename the endpoint" in prompt
    assert run.status is RunStatus.DONE  # gates, reviewer and policy again: direct now
    assert [d["mode"] for d in decisions(log, run)] == ["approval", "direct"]


@pytest.mark.integration
def test_hold_mode_with_a_remote_waits_locally_then_opens_a_pr(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    projects_dir: Path,
    registry: RunRegistry,
    repo: Path,
    project: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = GITHUB_URL
    settings.run.integration = "hold"
    save_project(settings, projects_dir=projects_dir)
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", TOKEN)
    fake = FakeGitHub(make_github_remote(repo, tmp_path / "remote.git"))
    files = {"hello.py": "x = 1\n" * 401}
    loop, _ = make_loop(
        [transcripts.implement(files)],
        [transcripts.review("approve")],
        integrator=Delivery(clock=clock, github=fake.client),
    )
    loop.start("demo", "next")
    loop.wait("demo")
    run = log_of(registry).list_runs()[0]
    assert run.policy is not None and run.policy["mode"] == "approval"
    assert [r["rule"] for r in run.policy["rules"]] == ["diff_size", "hold_mode"]

    loop.approve("demo", "T01")  # hold no longer applies; the size still needs a PR
    loop.wait("demo")

    run = log_of(registry).list_runs()[0]
    assert run.pr_number == 1
    assert run.policy == {
        "mode": "pr",
        "rules": [{"rule": "diff_size", "detail": "401 lines > 400"}],
        "approved_by_user": True,
    }


@pytest.mark.integration
def test_runs_that_block_never_reach_the_policy(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
) -> None:
    # Review retries used up: still blocked, as before.
    reviews = [transcripts.review("changes_requested", (True, False, True)) for _ in range(3)]
    loop, _ = make_loop(
        [transcripts.implement() for _ in range(3)], reviews, integrator=Delivery(clock=clock)
    )
    loop.start("demo", "next")
    loop.wait("demo")
    run = log_of(registry).list_runs()[0]
    assert (run.status, run.reason) == (RunStatus.BLOCKED, "changes requested after 2 retries")
    assert run.policy is None and decisions(log_of(registry), run) == []


@pytest.mark.integration
def test_failing_gates_never_ask_the_reviewer_or_the_policy(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
) -> None:
    reviewer = FakeRunner([transcripts.review("needs_human")])
    loop, _ = make_loop(
        [transcripts.implement() for _ in range(4)],
        reviewer,
        gates=[failing("test")] * 4,
        integrator=Delivery(clock=clock),
    )
    loop.start("demo", "T02")
    loop.wait("demo")
    run = log_of(registry).list_runs()[0]
    assert run.status is RunStatus.BLOCKED
    assert reviewer.calls == []
    assert run.policy is None and decisions(log_of(registry), run) == []
