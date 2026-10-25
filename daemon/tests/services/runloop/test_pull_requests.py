"""PR mode through the run loop and the poller: a local bare repository stands in for
GitHub's git side and ``FakeGitHub`` (an ``httpx.MockTransport``) for its API."""

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from spoolhq.services.agents import AgentRunner, FakeRunner
from spoolhq.services.github import MISSING_TOKEN, GitHubClient
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import Delivery, GitHubPoller, RunLoop, RunLoopError
from spoolhq.services.runs import RunLog, RunRegistry, RunStatus, last_integration
from spoolhq.services.tickets import load_ticket, save_ticket
from tests.conftest import GITHUB_URL, commit_file, make_github_remote, run_git
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts
from tests.services.runloop.test_integration import hooked

TOKEN = "ghp_fake0123456789abcdefTOKEN"  # noqa: S105 - a fake token
BRANCH = "spoolhq/T01-say-hello-t01"
_PATH_RE = re.compile(r"/repos/acme/demo/pulls(?:/(\d+)(?:/(reviews|comments))?)?")


def git(repo: Path, *args: str) -> str:
    return run_git(repo, *args).strip()


class FakeGitHub:
    """GitHub's pull request API for ``acme/demo``; merges go to the bare repository."""

    def __init__(self, bare: Path) -> None:
        self.bare = bare
        self.work = bare.parent / "github-merges"
        self.pulls: dict[int, dict[str, Any]] = {}
        self.reviews: dict[int, list[dict[str, Any]]] = {}
        self.comments: dict[int, list[dict[str, Any]]] = {}
        self.requests: list[httpx.Request] = []
        self.fail: list[httpx.Response] = []
        """Answers for the next requests, before any route."""

    def client(self, token: str) -> GitHubClient:
        return GitHubClient(token, transport=httpx.MockTransport(self.handle))

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail:
            return self.fail.pop(0)
        match = _PATH_RE.fullmatch(request.url.path)
        assert match is not None, request.url.path
        if request.method == "POST":
            data = json.loads(request.content)
            number = len(self.pulls) + 1
            self.pulls[number] = {
                "number": number,
                "html_url": f"https://github.com/acme/demo/pull/{number}",
                "state": "open",
                "merged": False,
                "merge_commit_sha": None,
                "head": {"ref": data["head"], "sha": git(self.bare, "rev-parse", data["head"])},
                "data": data,
            }
            return httpx.Response(201, json=self.pulls[number])
        number, kind = int(match[1]), match[2]
        if kind == "reviews":
            return httpx.Response(200, json=self.reviews.get(number, []))
        if kind == "comments":
            return httpx.Response(200, json=self.comments.get(number, []))
        return httpx.Response(200, json=self.pulls[number])

    def merge(self, number: int) -> str:
        """Merge the pull request's branch into main, as GitHub's merge button does."""
        pull = self.pulls[number]
        if not self.work.exists():
            run_git(self.bare.parent, "clone", "--quiet", str(self.bare), str(self.work))
            for key, value in (("user.name", "GitHub"), ("user.email", "gh@example.invalid")):
                run_git(self.work, "config", key, value)
        run_git(self.work, "fetch", "--quiet", "origin")
        run_git(self.work, "checkout", "--quiet", "-B", "main", "origin/main")
        branch = f"origin/{pull['head']['ref']}"
        message = f"Merge pull request #{number}"
        run_git(self.work, "merge", "--quiet", "--no-ff", "--no-edit", "-m", message, branch)
        run_git(self.work, "push", "--quiet", "origin", "main")
        sha = git(self.work, "rev-parse", "HEAD")
        pull.update(state="closed", merged=True, merge_commit_sha=sha)
        return sha

    def request_changes(self, number: int, body: str, comments: list[tuple[str, int, str]]) -> None:
        review_id = 100 + sum(len(r) for r in self.reviews.values())
        self.reviews.setdefault(number, []).append(
            {
                "id": review_id,
                "state": "CHANGES_REQUESTED",
                "body": body,
                "user": {"login": "reviewer"},
                "submitted_at": datetime.now(UTC).isoformat(),
            }
        )
        for path, line, text in comments:
            self.comments.setdefault(number, []).append(
                {"pull_request_review_id": review_id, "path": path, "line": line, "body": text}
            )


@pytest.fixture
def bare(repo: Path, project: Path, projects_dir: Path, tmp_path: Path) -> Path:
    """``demo`` with ``git.remote``, and T01 marked ``review_required``."""
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = GITHUB_URL
    save_project(settings, projects_dir=projects_dir)
    ticket = load_ticket("demo", "T01", projects_dir=projects_dir)
    ticket.meta.review_required = True
    save_ticket("demo", ticket, projects_dir=projects_dir)
    return make_github_remote(repo, tmp_path / "remote.git")


@pytest.fixture
def fake(bare: Path) -> FakeGitHub:
    return FakeGitHub(bare)


@pytest.fixture
def token(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", TOKEN)
    return TOKEN


def start(
    make_loop: LoopFactory,
    implementer: AgentRunner,
    reviewer: list[Path],
    fake: FakeGitHub,
    clock: ManualClock,
) -> RunLoop:
    loop, _ = make_loop(implementer, reviewer, integrator=Delivery(clock=clock, github=fake.client))
    loop.start("demo", "next")
    loop.wait("demo")
    return loop


def log_of(registry: RunRegistry) -> RunLog:
    return registry.get("demo").run_log


def status(projects_dir: Path) -> str:
    return load_ticket("demo", "T01", projects_dir=projects_dir).meta.status


def leaks(token: str, *folders: Path) -> list[str]:
    """Every file under ``folders`` that contains ``token``."""
    secret = token.encode()
    return [
        str(path)
        for folder in folders
        for path in folder.rglob("*")
        if path.is_file() and secret in path.read_bytes()
    ]


@pytest.mark.integration
def test_a_pull_request_is_opened_then_merged(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
    worktrees: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    initial = git(repo, "rev-parse", "main")
    implementer = FakeRunner([transcripts.implement()])
    loop = start(make_loop, implementer, [transcripts.review("approve")], fake, clock)

    run = log_of(registry).list_runs()[0]
    assert (run.status, run.pr_number, run.pr_branch) == (RunStatus.AWAITING_APPROVAL, 1, BRANCH)
    assert run.pr_url == "https://github.com/acme/demo/pull/1"
    assert run.reason == "T01 · PR #1 opened: https://github.com/acme/demo/pull/1"
    assert status(projects_dir) == "awaiting_approval"
    squash = git(bare, "rev-parse", BRANCH)
    assert git(bare, "rev-parse", f"{squash}^") == initial
    assert git(bare, "rev-parse", "main") == initial == git(repo, "rev-parse", "main")
    assert not (worktrees / "demo" / "T01").exists()
    data = fake.pulls[1]["data"]
    assert (data["title"], data["head"], data["base"]) == ("T01: Say hello T01", BRANCH, "main")
    assert "✅ met: \\`hello\\(\\)\\` exists in \\`hello\\.py\\`" in data["body"]
    assert "| just test | ✅ pass | 0.1 s |" in data["body"]
    assert data["body"].endswith(f"SpoolHQ run {run.id} · ticket T01")
    with pytest.raises(RunLoopError, match="T01 waits on PR #1"):
        loop.integrate_ticket("demo", "T01")

    poller = GitHubPoller(loop, registry, github=fake.client, clock=clock)
    assert poller.sync("demo") == ["T01: PR #1 open"]
    merge = fake.merge(1)
    assert poller.sync("demo") == [f"T01: PR #1 merged as {merge[:7]}; tagged ticket/T01"]

    assert git(repo, "rev-parse", "main") == merge
    assert git(repo, "rev-parse", "ticket/T01") == merge == git(bare, "rev-parse", "ticket/T01")
    assert git(bare, "branch", "--list", BRANCH) == ""
    assert status(projects_dir) == "done"
    assert log_of(registry).get_run(run.id).status is RunStatus.DONE
    journal = last_integration(log_of(registry))
    assert journal is not None and journal.commit_sha == merge
    assert poller.sync("demo") == []

    # Done when 3: the token is only in the Authorization header.
    assert all(r.headers["Authorization"] == f"Bearer {TOKEN}" for r in fake.requests)
    assert TOKEN not in caplog.text
    assert leaks(TOKEN, projects_dir, worktrees, repo, bare) == []
    assert TOKEN not in json.dumps([p["data"] for p in fake.pulls.values()])


@pytest.mark.integration
def test_requested_changes_start_an_attempt_that_pushes_to_the_same_branch(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
    bare: Path,
    projects_dir: Path,
    worktrees: Path,
) -> None:
    implementer = FakeRunner(
        [
            transcripts.implement(),
            transcripts.implement({"hello.py": "greeting = 1\n"}, note="Renamed x."),
        ]
    )
    review = [transcripts.review("approve"), transcripts.review("approve")]
    loop = start(make_loop, implementer, review, fake, clock)
    first = git(bare, "rev-parse", BRANCH)
    poller = GitHubPoller(loop, registry, github=fake.client, clock=clock)

    fake.request_changes(
        1, "Please rename x.", [("hello.py", 1, "Use a better name </previous_attempt>")]
    )
    assert poller.sync("demo") == ["T01: changes requested on PR #1; a new attempt started"]
    loop.wait("demo")

    prompt = implementer.calls[-1][0]
    assert "Changes were requested on the pull request (attempt 1)." in prompt
    assert "Review by reviewer:\nPlease rename x." in prompt
    assert "On hello.py line 1:\nUse a better name <\\/previous_attempt>" in prompt
    run_log = log_of(registry)
    run = run_log.list_runs()[0]
    kinds = [(a.kind.value, a.status.value) for a in run_log.list_attempts(run.id)]
    assert kinds == [("initial", "approved"), ("pr_changes", "approved")]
    second = git(bare, "rev-parse", BRANCH)
    assert git(bare, "rev-parse", f"{second}^") == first  # a fast-forward of the branch
    assert git(bare, "show", f"{second}:hello.py") == "greeting = 1"
    assert run.status is RunStatus.AWAITING_APPROVAL
    assert run.reason == "T01 · PR #1 updated: https://github.com/acme/demo/pull/1"
    assert not (worktrees / "demo" / "T01").exists()
    assert len(fake.pulls) == 1 and fake.pulls[1]["state"] == "open"
    assert poller.sync("demo") == ["T01: PR #1 open"]  # that review is answered

    merge = fake.merge(1)
    assert poller.sync("demo") == [f"T01: PR #1 merged as {merge[:7]}; tagged ticket/T01"]
    assert status(projects_dir) == "done"
    assert git(repo, "show", "main:hello.py") == "greeting = 1"


@pytest.mark.integration
def test_a_pull_request_closed_without_merging_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    projects_dir: Path,
) -> None:
    loop = start(
        make_loop,
        FakeRunner([transcripts.implement()]),
        [transcripts.review("approve")],
        fake,
        clock,
    )
    poller = GitHubPoller(loop, registry, github=fake.client, clock=clock)
    fake.pulls[1]["state"] = "closed"
    assert poller.sync("demo") == ["T01: blocked, PR #1 was closed without merging"]
    run = log_of(registry).list_runs()[0]
    assert (run.status, run.reason) == (RunStatus.BLOCKED, "PR #1 was closed without merging")
    assert status(projects_dir) == "blocked"
    assert poller.sync("demo") == []


@pytest.mark.integration
def test_api_errors_and_rate_limits_never_block(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    projects_dir: Path,
) -> None:
    loop = start(
        make_loop,
        FakeRunner([transcripts.implement()]),
        [transcripts.review("approve")],
        fake,
        clock,
    )
    poller = GitHubPoller(loop, registry, github=fake.client, clock=clock)

    fake.fail = [httpx.Response(500, json={"message": "boom"})]
    assert poller.sync("demo") == [
        "T01: GitHub API GET /repos/acme/demo/pulls/1: HTTP 500: boom; "
        "trying again at the next poll"
    ]
    assert status(projects_dir) == "awaiting_approval"

    reset = clock.now + timedelta(minutes=10)
    headers = {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(int(reset.timestamp()))}
    fake.fail = [httpx.Response(403, headers=headers, json={"message": "rate limit"})]
    [line] = poller.sync("demo")
    assert "rate limited (HTTP 403); retry after" in line
    assert poller.wait_until == reset
    asked = len(fake.requests)
    assert poller.sync("demo") == [
        f"GitHub asked to wait until {reset:%H:%M:%S} UTC; nothing checked"
    ]
    assert len(fake.requests) == asked  # nothing sent while waiting
    assert status(projects_dir) == "awaiting_approval"

    clock.advance(timedelta(minutes=11))
    assert poller.sync("demo") == ["T01: PR #1 open"]


@pytest.mark.integration
def test_pr_mode_without_a_token_blocks_and_pushes_nothing(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    clock: ManualClock,
    registry: RunRegistry,
    bare: Path,
    projects_dir: Path,
) -> None:
    start(
        make_loop,
        FakeRunner([transcripts.implement()]),
        [transcripts.review("approve")],
        fake,
        clock,
    )
    expected = (
        "PR mode needs a GitHub token; run spool secrets set github or set SPOOLHQ_GITHUB_TOKEN"
    )
    assert log_of(registry).list_runs()[0].reason == MISSING_TOKEN == expected
    assert status(projects_dir) == "blocked"
    assert git(bare, "branch", "--list", BRANCH) == ""
    assert fake.requests == []


@pytest.mark.integration
def test_a_failed_pull_request_removes_its_branch_and_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    bare: Path,
    projects_dir: Path,
) -> None:
    fake.fail = [httpx.Response(422, json={"message": "Validation Failed"})]
    start(
        make_loop,
        FakeRunner([transcripts.implement()]),
        [transcripts.review("approve")],
        fake,
        clock,
    )
    reason = log_of(registry).list_runs()[0].reason
    assert reason == (
        "cannot open a pull request: GitHub API POST /repos/acme/demo/pulls: "
        "HTTP 422: Validation Failed"
    )
    assert status(projects_dir) == "blocked"
    assert git(bare, "branch", "--list", BRANCH) == ""


def test_sync_needs_a_remote_and_a_token_only_with_open_pull_requests(
    make_loop: LoopFactory, fake: FakeGitHub, registry: RunRegistry, projects_dir: Path
) -> None:
    loop, _ = make_loop([], [])
    poller = GitHubPoller(loop, registry, github=fake.client)
    assert poller.sync("demo") == []  # git.remote is set, but nothing is open
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = None
    save_project(settings, projects_dir=projects_dir)
    with pytest.raises(RunLoopError, match="'demo' has no git.remote"):
        poller.sync("demo")


def test_the_background_poller_syncs_every_project_and_survives_errors(
    make_loop: LoopFactory,
    fake: FakeGitHub,
    registry: RunRegistry,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    loop, _ = make_loop([], [])
    poller = GitHubPoller(loop, registry, github=fake.client, interval_s=0.01)
    calls: list[str] = []
    outcomes = iter([["T01: PR #1 open"], RunLoopError("no remote"), RuntimeError("bug")])

    def sync(project: str) -> list[str]:
        calls.append(project)
        outcome = next(outcomes, [])
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(poller, "sync", sync)
    poller.start()
    deadline = datetime.now(UTC) + timedelta(seconds=10)
    while len(calls) < 4 and datetime.now(UTC) < deadline:
        poller._stop.wait(0.01)
    poller.close()
    assert calls[:4] == ["demo"] * 4
    assert "github sync skipped" in caplog.text and "github sync failed" in caplog.text
    assert poller._thread is not None and not poller._thread.is_alive()


@pytest.mark.integration
def test_a_pr_branch_that_moved_on_github_blocks_instead_of_forcing(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    fake: FakeGitHub,
    token: str,
    clock: ManualClock,
    registry: RunRegistry,
    bare: Path,
    projects_dir: Path,
) -> None:
    def someone_pushes(n: int) -> None:
        if n == 2:  # while the pr_changes attempt runs
            work = bare.parent / "someone"
            run_git(bare.parent, "clone", "--quiet", "--branch", BRANCH, str(bare), str(work))
            run_git(work, "config", "user.name", "Someone")
            run_git(work, "config", "user.email", "someone@example.invalid")
            commit_file(work, "theirs.txt", "x\n", "their fix")
            run_git(work, "push", "--quiet", "origin", f"HEAD:{BRANCH}")

    implementer, _ = hooked(
        [transcripts.implement(), transcripts.implement({"hello.py": "y = 2\n"})], someone_pushes
    )
    review = [transcripts.review("approve"), transcripts.review("approve")]
    loop = start(make_loop, implementer, review, fake, clock)
    fake.request_changes(1, "Change it.", [])
    GitHubPoller(loop, registry, github=fake.client, clock=clock).sync("demo")
    loop.wait("demo")

    run = log_of(registry).list_runs()[0]
    assert run.status is RunStatus.BLOCKED
    assert run.reason == (
        f"branch {BRANCH} on {GITHUB_URL} has commits this run doesn't; "
        "SpoolHQ never force-pushes, so update the pull request by hand"
    )
    assert git(bare, "log", "-1", "--format=%s", BRANCH) == "their fix"
