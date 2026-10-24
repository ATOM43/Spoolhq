"""LocalIntegrator through the run loop: real temporary repos, fake agents and gates."""

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from spoolhq.services.agents import AgentPolicy, FakeRunner
from spoolhq.services.gates import run_gates
from spoolhq.services.git import GitError
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import LocalIntegrator, RunLoop, RunLoopError, integration
from spoolhq.services.runs import EventKind, RunLog, RunRegistry, RunStatus, open_integrations
from spoolhq.services.tickets import load_ticket
from tests.conftest import commit_file, run_git
from tests.services.runloop.conftest import (
    PASSING,
    Hooked,
    LoopFactory,
    ManualClock,
    Transcripts,
    failing,
)

TITLE = "Say hello T01"


def log_of(registry: RunRegistry) -> RunLog:
    return registry.get("demo").run_log


def status(projects_dir: Path, ticket_id: str = "T01") -> str:
    return load_ticket("demo", ticket_id, projects_dir=projects_dir).meta.status


def git(repo: Path, *args: str) -> str:
    return run_git(repo, *args).strip()


def subjects(repo: Path) -> list[str]:
    return git(repo, "log", "--format=%s", "main").splitlines()


def kinds(log: RunLog, run_id: int) -> list[tuple[str, str]]:
    return [(a.kind.value, a.status.value) for a in log.list_attempts(run_id)]


def run(loop: RunLoop, mode: str = "next") -> int:
    started = loop.start("demo", mode)  # type: ignore[arg-type]
    loop.wait("demo")
    return started.id


def hooked(transcripts: list[Path], before: Callable[[int], object]) -> tuple[Hooked, FakeRunner]:
    """A FakeRunner that calls ``before(n)`` before its n-th run (1-based)."""
    fake = FakeRunner(transcripts)
    count = [0]

    def call(_policy: AgentPolicy) -> None:
        count[0] += 1
        before(count[0])

    return Hooked(fake, call), fake


def on_first(action: Callable[[], object]) -> Callable[[int], None]:
    """A ``hooked`` callback that runs ``action`` before the first run only."""

    def call(n: int) -> None:
        if n == 1:
            action()

    return call


@pytest.fixture
def local(clock: ManualClock) -> LocalIntegrator:
    return LocalIntegrator(clock=clock)


# --- Done when 1: three tickets, three commits ----------------------------------------

MODULE = "def f{n}() -> int:\n    return {n}\n"
TEST = "from mod{n} import f{n}\n\n\ndef test_f{n}() -> None:\n    assert f{n}() == {n}\n"


@pytest.mark.integration
def test_three_tickets_give_three_squash_commits_with_green_gates(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
    local: LocalIntegrator,
    tmp_path: Path,
) -> None:
    implement = [
        transcripts.implement(
            {f"mod{n}.py": MODULE.format(n=n), f"test_mod{n}.py": TEST.format(n=n)},
            note=f"Added mod{n} and its test.",
        )
        for n in (1, 2, 3)
    ]
    loop, _ = make_loop(implement, [transcripts.review("approve")] * 3, integrator=local)
    initial = git(repo, "rev-parse", "main")

    run(loop, "all")

    log = log_of(registry)
    runs = sorted(log.list_runs(), key=lambda r: r.id)
    assert [(r.ticket_id, r.status) for r in runs] == [
        (t, RunStatus.DONE) for t in ("T01", "T02", "T03")
    ]
    commits = git(repo, "rev-list", "--reverse", f"{initial}..main").splitlines()
    assert len(commits) == 3
    parent = initial
    for n, (sha, r) in enumerate(zip(commits, runs, strict=True), start=1):
        tid = f"T0{n}"
        assert git(repo, "rev-parse", f"{sha}^") == parent  # squash: one parent, the old main
        assert len(git(repo, "rev-list", "--parents", "-n", "1", sha).split()) == 2
        message = git(repo, "log", "-1", "--format=%B", sha)
        assert message.splitlines()[0] == f"{tid}: Say hello {tid}"
        assert message.endswith(f"SpoolHQ-Ticket: {tid}\nSpoolHQ-Run: {r.id}")
        assert f"Added mod{n} and its test." in message
        assert git(repo, "rev-parse", f"ticket/{tid}^{{commit}}") == sha
        files = git(repo, "show", "--name-only", "--format=", sha).split()
        assert sorted(files) == ["PROGRESS.md", f"mod{n}.py", f"test_mod{n}.py"]
        progress = git(repo, "show", f"{sha}:PROGRESS.md")
        assert progress.count("\n## ") == n
        assert progress.startswith("# Progress\n")
        assert progress.endswith(
            f"## {tid} · Say hello {tid} (2026-10-18)\n\nAdded mod{n} and its test."
        )
        parent = sha

        # The gates pass when rerun at each commit.
        checkout = tmp_path / f"at-{n}"
        run_git(repo, "worktree", "add", "--quiet", "--detach", str(checkout), sha)
        py = Path(sys.executable).as_posix()
        commands = {
            "install": f"{py} -c pass",
            "lint": f"{py} -m compileall -q .",
            "test": f"{py} -m pytest -q -p no:cacheprovider",
        }
        timeouts = {"install": 60, "lint": 60, "test": 120}
        assert run_gates(checkout, commands, timeouts, tmp_path / f"logs-{n}").passed
        run_git(repo, "worktree", "remove", "--force", str(checkout))

    assert git(repo, "tag", "--list", "ticket/*").split() == [
        "ticket/T01",
        "ticket/T02",
        "ticket/T03",
    ]
    assert git(repo, "branch", "--list", "feat/*") == ""
    assert not any((worktrees / "demo" / t).exists() for t in ("T01", "T02", "T03"))
    assert all(status(projects_dir, t) == "done" for t in ("T01", "T02", "T03"))
    assert git(repo, "status", "--porcelain") == ""
    assert open_integrations(log) == []
    events = [e for e in log.events_since(0) if e.kind is EventKind.INTEGRATE]
    assert [e.payload["tag"] for e in events] == ["ticket/T01", "ticket/T02", "ticket/T03"]
    assert [e.payload["commit"] for e in events] == commits


# --- main moved ------------------------------------------------------------------------


def test_main_moved_before_integration_is_merged_in_and_gated(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    moved: list[str] = []
    reviewer, _ = hooked(
        [transcripts.review("approve")],
        lambda n: moved.append(commit_file(repo, "other.py", "y = 1\n", "someone else")),
    )
    loop, gates = make_loop([transcripts.implement()], reviewer, integrator=local)

    run_id = run(loop)

    assert log_of(registry).get_run(run_id).status is RunStatus.DONE
    assert len(gates.calls) == 2  # the attempt, then again on the merged code
    head = git(repo, "rev-parse", "main")
    assert git(repo, "rev-parse", f"{head}^") == moved[0]
    assert sorted(git(repo, "show", "--name-only", "--format=", head).split()) == [
        "PROGRESS.md",
        "hello.py",
    ]
    assert (repo / "other.py").is_file() and (repo / "hello.py").is_file()


def test_gates_failing_after_the_merge_use_a_gate_retry(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    reviewer, _ = hooked(
        [transcripts.review("approve"), transcripts.review("approve")],
        on_first(lambda: commit_file(repo, "other.py", "y = 1\n", "someone else")),
    )
    loop, _ = make_loop(
        [transcripts.implement(), transcripts.implement({"hello.py": "x = 2\n"})],
        reviewer,
        gates=[PASSING, failing("test_other.py::test_y"), PASSING],
        integrator=local,
    )

    run_id = run(loop)

    log = log_of(registry)
    assert log.get_run(run_id).status is RunStatus.DONE
    assert kinds(log, run_id) == [("initial", "approved"), ("gate_retry", "approved")]
    retry_prompt = loop.agents.implementer.calls[1][0]  # type: ignore[attr-defined]
    assert "`test_other.py::test_y`" in retry_prompt
    assert git(repo, "show", "main:hello.py") == "x = 2"


@pytest.mark.parametrize("moves", [1, 3])
def test_main_moving_during_the_advance_retries_then_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
    clock: ManualClock,
    moves: int,
) -> None:
    done: list[str] = []

    def checkpoint(state: str) -> None:
        if state == "committed" and len(done) < moves:
            done.append(commit_file(repo, f"other{len(done)}.py", "y\n", f"move {len(done)}"))

    integrator = LocalIntegrator(clock=clock, checkpoint=checkpoint)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=integrator
    )

    run_id = run(loop)

    final = log_of(registry).get_run(run_id)
    if moves == 3:
        assert (final.status, final.reason) == (
            RunStatus.BLOCKED,
            "main kept moving during integration",
        )
        assert git(repo, "rev-parse", "main") == done[-1]
        assert not git(repo, "tag", "--list")
        path = worktrees / "demo" / "T01"
        assert git(path, "symbolic-ref", "HEAD") == "refs/heads/feat/T01-say-hello-t01"
        assert status(projects_dir) == "blocked"
    else:
        assert final.status is RunStatus.DONE
        assert subjects(repo)[:2] == [f"T01: {TITLE}", "move 0"]
    assert open_integrations(log_of(registry)) == []


# --- conflicts -------------------------------------------------------------------------


def test_conflict_goes_back_to_the_implementer_once(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    implementer, fake = hooked(
        [
            transcripts.implement({"hello.py": "x = 1\n"}),
            transcripts.implement({"hello.py": "x = 2\n"}),
        ],
        on_first(lambda: commit_file(repo, "hello.py", "x = 0\n", "main's hello")),
    )
    loop, _ = make_loop(
        implementer,
        [transcripts.review("approve"), transcripts.review("approve")],
        integrator=local,
    )

    run_id = run(loop)

    log = log_of(registry)
    assert log.get_run(run_id).status is RunStatus.DONE
    assert kinds(log, run_id) == [("initial", "approved"), ("conflict_retry", "approved")]
    prompt = fake.calls[1][0]
    assert "Your changes conflict with the latest main (attempt 1)." in prompt
    assert "Files with conflicts:\n\n- `hello.py`" in prompt
    assert "Note from SpoolHQ:\n\nSpoolHQ merged the latest main" in prompt
    assert git(repo, "show", "main:hello.py") == "x = 2"
    assert subjects(repo)[:2] == [f"T01: {TITLE}", "main's hello"]


def test_markers_left_behind_block(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    worktrees: Path,
    local: LocalIntegrator,
) -> None:
    markers = "<<<<<<< ours\nx = 1\n=======\nx = 0\n>>>>>>> theirs\n"
    implementer, _ = hooked(
        [
            transcripts.implement({"hello.py": "x = 1\n"}),
            transcripts.implement({"hello.py": markers}),
        ],
        on_first(lambda: commit_file(repo, "hello.py", "x = 0\n", "main's hello")),
    )
    loop, _ = make_loop(implementer, [transcripts.review("approve")], integrator=local)

    run_id = run(loop)

    log = log_of(registry)
    final = log.get_run(run_id)
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "merge conflict with main in: hello.py",
    )
    assert kinds(log, run_id) == [("initial", "approved"), ("conflict_retry", "conflict")]
    assert subjects(repo)[0] == "main's hello"
    assert (worktrees / "demo" / "T01").is_dir()  # kept for inspection


def test_a_second_conflict_blocks(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    implementer, _ = hooked(
        [
            transcripts.implement({"hello.py": "x = 1\n"}),
            transcripts.implement({"hello.py": "x = 2\n"}),
        ],
        lambda n: commit_file(repo, "hello.py", f"x = {n * 10}\n", f"main's hello {n}"),
    )
    loop, _ = make_loop(
        implementer,
        [transcripts.review("approve"), transcripts.review("approve")],
        integrator=local,
    )

    run_id = run(loop)

    final = log_of(registry).get_run(run_id)
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "merge conflict with main in: hello.py",
    )
    assert subjects(repo)[0] == "main's hello 2"


# --- the main checkout ----------------------------------------------------------------


def test_a_dirty_main_checkout_waits_then_integrates(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    local: LocalIntegrator,
) -> None:
    notes = repo / "notes.txt"
    reviewer, _ = hooked(
        [transcripts.review("approve")], lambda n: notes.write_text("mine\n", encoding="utf-8")
    )
    loop, _ = make_loop([transcripts.implement()], reviewer, integrator=local)
    before = git(repo, "rev-parse", "main")

    run_id = run(loop)

    log = log_of(registry)
    final = log.get_run(run_id)
    assert (final.status, final.reason) == (
        RunStatus.AWAITING_APPROVAL,
        f"main checkout has uncommitted changes in {repo.resolve()}; commit or stash them, "
        "then run spool run integrate demo T01",
    )
    assert status(projects_dir) == "awaiting_approval"
    assert notes.read_text(encoding="utf-8") == "mine\n"
    assert git(repo, "rev-parse", "main") == before
    assert git(repo, "status", "--porcelain") == "?? notes.txt"

    with pytest.raises(RunLoopError, match="T01 is awaiting_approval"):
        loop.start("demo", "next", "T01")
    with pytest.raises(RunLoopError, match="T02 is ready, not awaiting approval"):
        loop.integrate_ticket("demo", "T02")

    notes.unlink()
    loop.integrate_ticket("demo", "T01")
    loop.wait("demo")

    assert log.get_run(run_id).status is RunStatus.DONE
    assert status(projects_dir) == "done"
    assert subjects(repo)[0] == f"T01: {TITLE}"


# --- the diff guard -------------------------------------------------------------------


def test_build_junk_is_left_out_and_listed(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    files = {
        "hello.py": "x = 1\n",
        "__pycache__/x.pyc": "junk",
        "node_modules/a.js": "junk",
        ".env.example": "TOKEN=\n",
    }
    loop, _ = make_loop(
        [transcripts.implement(files)], [transcripts.review("approve")], integrator=local
    )

    run_id = run(loop)

    log = log_of(registry)
    assert log.get_run(run_id).status is RunStatus.DONE
    committed = git(repo, "show", "--name-only", "--format=", "main").split()
    assert sorted(committed) == [".env.example", "PROGRESS.md", "hello.py"]
    listed = [e.payload for e in log.events_since(0, run_id=run_id) if e.kind is EventKind.LOG]
    assert listed == [
        {
            "message": "build files left out of the commit",
            "files": ["__pycache__/x.pyc", "node_modules/a.js"],
            "count": 2,
        }
    ]
    assert not (repo / "node_modules").exists()


@pytest.mark.parametrize(
    ("files", "reason"),
    [
        ({".env": "TOKEN=x\n"}, "refusing to commit likely secrets: .env"),
        ({"big.bin": "x" * (6 * 1024 * 1024)}, "file too large to commit: big.bin (6.0 MB)"),
    ],
)
def test_secrets_and_large_files_block(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    worktrees: Path,
    local: LocalIntegrator,
    files: dict[str, str],
    reason: str,
) -> None:
    loop, _ = make_loop(
        [transcripts.implement({"hello.py": "x = 1\n", **files})],
        [transcripts.review("approve")],
        integrator=local,
    )
    before = git(repo, "rev-parse", "main")

    run_id = run(loop)

    final = log_of(registry).get_run(run_id)
    assert (final.status, final.reason) == (RunStatus.BLOCKED, reason)
    assert git(repo, "rev-parse", "main") == before
    path = worktrees / "demo" / "T01"
    assert git(path, "symbolic-ref", "HEAD") == "refs/heads/feat/T01-say-hello-t01"
    assert git(path, "status", "--porcelain") == ""


def test_an_existing_tag_blocks_before_main_moves(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    local: LocalIntegrator,
) -> None:
    run_git(repo, "tag", "ticket/T01")
    before = git(repo, "rev-parse", "main")
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=local
    )

    run_id = run(loop)

    final = log_of(registry).get_run(run_id)
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "tag ticket/T01 already exists; delete it or rename the ticket",
    )
    assert git(repo, "rev-parse", "main") == before


# --- hold mode ------------------------------------------------------------------------


def test_hold_mode_keeps_the_approved_ticket_until_integrate(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    worktrees: Path,
    local: LocalIntegrator,
) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    settings.run.integration = "hold"
    save_project(settings, projects_dir=projects_dir)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=local
    )
    before = git(repo, "rev-parse", "main")

    run_id = run(loop, "all")

    log = log_of(registry)
    final = log.get_run(run_id)
    path = worktrees / "demo" / "T01"
    assert (final.status, final.reason) == (
        RunStatus.AWAITING_APPROVAL,
        f"T01 approved; merge it with `spool run integrate demo T01` — worktree kept at {path}",
    )
    assert git(repo, "rev-parse", "main") == before
    assert status(projects_dir, "T02") == "ready"  # run all stopped there

    loop.integrate_ticket("demo", "T01")
    loop.wait("demo")

    assert log.get_run(run_id).status is RunStatus.DONE
    assert subjects(repo)[0] == f"T01: {TITLE}"
    assert not path.exists()


def test_a_git_failure_mid_squash_restores_the_worktree(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    registry: RunRegistry,
    repo: Path,
    worktrees: Path,
    local: LocalIntegrator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(path: Path, message: str) -> str:
        raise GitError("git commit failed (exit 1): disk full")

    monkeypatch.setattr(integration, "commit_staged", broken)
    loop, _ = make_loop(
        [transcripts.implement()], [transcripts.review("approve")], integrator=local
    )
    before = git(repo, "rev-parse", "main")

    run_id = run(loop)

    final = log_of(registry).get_run(run_id)
    assert (final.status, final.reason) == (
        RunStatus.BLOCKED,
        "internal error: git commit failed (exit 1): disk full",
    )
    assert git(repo, "rev-parse", "main") == before
    path = worktrees / "demo" / "T01"
    assert git(path, "symbolic-ref", "HEAD") == "refs/heads/feat/T01-say-hello-t01"
    assert git(path, "status", "--porcelain") == ""
    assert open_integrations(log_of(registry)) == []
