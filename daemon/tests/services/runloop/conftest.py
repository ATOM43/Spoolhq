"""Run loop fixtures: a project with tickets, generated agent transcripts, fake gates."""

import json
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentPolicy,
    AgentRunner,
    BackendInfo,
    Budget,
    FakeRunner,
    RunResult,
)
from spoolhq.services.agents.runner import EventCallback, RawCallback
from spoolhq.services.gates import GateName, GateResult, GateRun, GateStatus
from spoolhq.services.projects import init_project
from spoolhq.services.runloop import (
    Agents,
    IntegrationResult,
    IntegrationStatus,
    Integrator,
    RunContext,
    RunLoop,
)
from spoolhq.services.runs import RunRegistry
from spoolhq.services.scheduler import apply_transition
from tests.conftest import commit_file, run_git

RESET_EPOCH = 1792317600  # 2026-10-18T10:00:00Z
RESET_AT = datetime.fromtimestamp(RESET_EPOCH, UTC)

INIT_TOOLS = ["Bash", "Edit", "Glob", "Grep", "Read", "Write"]
REVIEW_TOOLS = ["Glob", "Grep", "Read"]


# --- transcripts -----------------------------------------------------------------------


def _init(tools: list[str]) -> dict[str, Any]:
    return {
        "type": "system",
        "subtype": "init",
        "tools": tools,
        "mcp_servers": [],
        "model": "claude-test-model",
        "permissionMode": "dontAsk",
        "claude_code_version": "2.1.302",
    }


def _assistant(content: list[dict[str, Any]], tokens: int, msg_id: str) -> dict[str, Any]:
    usage = {
        "input_tokens": tokens,
        "output_tokens": tokens // 4,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    message = {"id": msg_id, "role": "assistant", "content": content, "usage": usage}
    return {"type": "assistant", "message": message}


def _result(text: str, tokens: int, subtype: str = "success", **extra: Any) -> dict[str, Any]:
    return {
        "type": "result",
        "subtype": subtype,
        "is_error": subtype != "success",
        "num_turns": 2,
        "usage": {
            "input_tokens": tokens,
            "output_tokens": tokens // 4,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
        "permission_denials": [],
        "result": text,
        **extra,
    }


class Transcripts:
    """Writes stream-json transcripts for ``FakeRunner`` into a temp folder."""

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        folder.mkdir()
        self.count = 0

    def _write(self, lines: list[dict[str, Any]]) -> Path:
        self.count += 1
        path = self.folder / f"t{self.count:03d}.jsonl"
        path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
        return path

    def implement(
        self,
        files: Mapping[str, str] | None = None,
        *,
        note: str = "Added hello.",
        tokens: int = 1000,
        outcome: str = "success",
    ) -> Path:
        """An implementer run writing ``files``; ``outcome``: success, usage_limit,
        error, policy_violation or max_turns."""
        if outcome == "policy_violation":
            return self._write([{**_init([*INIT_TOOLS, "WebFetch"])}])
        writes = [
            {
                "type": "tool_use",
                "id": f"w{i}",
                "name": "Write",
                "input": {"file_path": p, "content": c},
            }
            for i, (p, c) in enumerate((files or {"hello.py": "x = 1\n"}).items())
        ]
        lines = [_init(INIT_TOOLS), _assistant(writes, tokens, "m1")]
        if outcome == "usage_limit":
            info = {"status": "rejected", "resetsAt": RESET_EPOCH, "rateLimitType": "five_hour"}
            lines.append({"type": "rate_limit_event", "rate_limit_info": info})
            lines.append(_result(f"Claude AI usage limit reached|{RESET_EPOCH}", 0, is_error=True))
        elif outcome == "error":
            lines.append(_result("", 0, "error_during_execution", errors=["API Error: 500"]))
        elif outcome == "max_turns":
            lines.append(_result("", tokens, "error_max_turns"))
        else:
            lines.append(_result(f"Done.\n<progress>{note}</progress>", tokens))
        return self._write(lines)

    def review(
        self,
        verdict: str,
        met: Sequence[bool] = (True, True, True),
        reasons: Sequence[str] | None = None,
        *,
        tokens: int = 500,
        outcome: str = "success",
    ) -> Path:
        """A reviewer run ending with a ``<verdict>`` block."""
        if outcome == "usage_limit":
            info = {"status": "rejected", "resetsAt": RESET_EPOCH, "rateLimitType": "five_hour"}
            return self._write(
                [
                    _init(REVIEW_TOOLS),
                    {"type": "rate_limit_event", "rate_limit_info": info},
                    _result(f"Claude AI usage limit reached|{RESET_EPOCH}", 0, is_error=True),
                ]
            )
        items = [
            {"index": i, "met": ok, "reason": (reasons[i - 1] if reasons else f"item {i} ok")}
            for i, ok in enumerate(met, start=1)
        ]
        body = json.dumps({"items": items, "verdict": verdict, "summary": f"{verdict}."})
        text = f"Reviewed.\n<verdict>{body}</verdict>"
        return self._write(
            [
                _init(REVIEW_TOOLS),
                _assistant([{"type": "text", "text": text}], tokens, "r1"),
                _result(text, tokens),
            ]
        )


@pytest.fixture
def transcripts(tmp_path: Path) -> Transcripts:
    return Transcripts(tmp_path / "transcripts")


# --- gates, clock, integrator ------------------------------------------------------------


def gate_result(name: GateName, status: GateStatus, failing: Sequence[str] = ()) -> GateResult:
    return GateResult(
        name=name,
        command=f"just {name}",
        status=status,
        exit_code=0 if status is GateStatus.PASSED else 1,
        duration_s=0.1,
        excerpt="" if status is GateStatus.PASSED else f"FAILED {' '.join(failing)}",
        failing_tests=tuple(failing),
        output_lines=3,
        output_truncated=False,
        log_path=None,
    )


PASSING = GateRun(tuple(gate_result(n, GateStatus.PASSED) for n in ("install", "lint", "test")))


def failing(*tests: str) -> GateRun:
    return GateRun(
        (
            gate_result("install", GateStatus.PASSED),
            gate_result("lint", GateStatus.PASSED),
            gate_result("test", GateStatus.FAILED, tests),
        )
    )


@dataclass
class FakeGates:
    """Returns ``runs`` in order (the last one repeats) and records each worktree."""

    runs: list[GateRun] = field(default_factory=lambda: [PASSING])
    calls: list[Path] = field(default_factory=list)

    def __call__(
        self, worktree: Path, commands: Mapping[str, str], timeouts: Mapping[str, float], log: Path
    ) -> GateRun:
        self.calls.append(worktree)
        return self.runs[min(len(self.calls) - 1, len(self.runs) - 1)]


class ManualClock:
    def __init__(self, now: datetime = datetime(2026, 10, 18, 9, 0, tzinfo=UTC)) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def advance(self, delta: timedelta) -> None:
        self.now += delta


class Merging:
    """The test integrator: merged, and marks the ticket done."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.commits: dict[str, list[str]] = {}
        """Each ticket's commit subjects on its run branch, at integration time."""

    def integrate(self, ctx: RunContext) -> IntegrationResult:
        self.calls.append(ctx.ticket_id)
        log = run_git(ctx.worktree.path, "log", "--format=%s", f"{ctx.worktree.base_sha}..HEAD")
        self.commits[ctx.ticket_id] = log.splitlines()
        apply_transition(ctx.project.name, ctx.ticket_id, "done", projects_dir=ctx.projects_dir)
        return IntegrationResult(IntegrationStatus.MERGED)


class Hooked:
    """An ``AgentRunner`` that calls ``before(policy)`` and then delegates to ``inner``."""

    def __init__(self, inner: AgentRunner, before: Callable[[AgentPolicy], None]) -> None:
        self.inner, self.before, self.name = inner, before, inner.name

    def detect(self) -> BackendInfo:
        return self.inner.detect()

    def run(
        self,
        prompt: str,
        policy: AgentPolicy,
        budget: Budget,
        *,
        model: str | None = None,
        on_event: EventCallback,
        on_raw: RawCallback | None = None,
        cancel: threading.Event,
    ) -> RunResult:
        self.before(policy)
        return self.inner.run(
            prompt, policy, budget, model=model, on_event=on_event, on_raw=on_raw, cancel=cancel
        )


# --- the project ------------------------------------------------------------------------

TICKET = """\
---
id: {id}
title: {title}
phase: 1
depends_on: [{deps}]
status: {status}
estimate_h: 1
---

## Scope
Add `hello()` to `hello.py`.

## Done when
- [ ] `hello()` exists in `hello.py`
- [ ] A test covers hello
- [ ] `just test` passes
"""


def write_ticket(
    workspace: Path, ticket_id: str, *, status: str = "ready", deps: Sequence[str] = ()
) -> None:
    text = TICKET.format(
        id=ticket_id, title=f"Say hello {ticket_id}", deps=", ".join(deps), status=status
    )
    (workspace / "tickets" / f"{ticket_id}-say-hello.md").write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path, isolated_git: None) -> Path:
    path = tmp_path / "repo"
    path.mkdir()
    run_git(path, "init", "--quiet", "-b", "main")
    run_git(path, "config", "user.name", "SpoolHQ Tests")
    run_git(path, "config", "user.email", "tests@example.invalid")
    run_git(path, "config", "commit.gpgsign", "false")
    commit_file(path, "README.md", "# demo\n", "initial commit")
    return path


@pytest.fixture
def project(repo: Path, projects_dir: Path) -> Path:
    """Workspace ``demo`` with ready tickets T01, T02 and T03."""
    workspace = init_project("demo", repo, projects_dir=projects_dir).path
    (workspace / "tickets").mkdir(exist_ok=True)
    for ticket_id in ("T01", "T02", "T03"):
        write_ticket(workspace, ticket_id)
    return workspace


@pytest.fixture
def worktrees(tmp_path: Path) -> Path:
    return tmp_path / "worktrees"


@pytest.fixture
def clock() -> ManualClock:
    return ManualClock()


@pytest.fixture
def registry(project: Path, projects_dir: Path) -> Iterator[RunRegistry]:
    runs = RunRegistry.start(projects_dir, daemon_instance="test")
    yield runs
    runs.close()


LoopFactory = Callable[..., tuple[RunLoop, FakeGates]]


@pytest.fixture
def make_loop(
    registry: RunRegistry, projects_dir: Path, worktrees: Path, home: Path, clock: ManualClock
) -> Iterator[LoopFactory]:
    loops: list[RunLoop] = []

    def make(
        implementer: AgentRunner | Sequence[Path],
        reviewer: AgentRunner | Sequence[Path] = (),
        *,
        gates: Sequence[GateRun] = (PASSING,),
        integrator: Integrator | None = None,
    ) -> tuple[RunLoop, FakeGates]:
        fake_gates = FakeGates(list(gates))
        loop = RunLoop(
            registry,
            projects_dir=projects_dir,
            worktrees_dir=worktrees,
            home=home,
            agents=Agents(
                implementer if not isinstance(implementer, Sequence) else FakeRunner(implementer),
                reviewer if not isinstance(reviewer, Sequence) else FakeRunner(reviewer),
            ),
            integrator=integrator if integrator is not None else Merging(),
            clock=clock,
            gates=fake_gates,
            poll_s=3600,
        )
        loops.append(loop)
        return loop, fake_gates

    yield make
    for loop in loops:
        loop.close()
