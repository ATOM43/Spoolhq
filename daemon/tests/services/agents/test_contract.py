"""The contract every agent adapter must pass, over a list of adapter cases.

Each case builds a runner that plays a recorded scenario: the Claude Code adapter
through the fake ``claude`` binary, the Codex CLI adapter through the same binary as
``codex``, and the fake runner directly. Adding an adapter means adding one
``AdapterCase``; its scenarios are the recorded transcripts in
``tests/fixtures/agents/claude/``, or its own recordings of the same runs
(``tests/fixtures/agents/codex/``).
"""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentRunner,
    Budget,
    ClaudeCliRunner,
    CodexCliRunner,
    FakeRunner,
    FileEdit,
    Outcome,
    PermissionDenied,
    RunResult,
    Started,
    Usage,
)
from tests.conftest import (
    AGENT_FIXTURES,
    AGENT_PROMPT,
    CODEX_FIXTURES,
    fake_claude_cmd,
    fake_codex_cmd,
    sandbox_which,
)
from tests.services.agents.test_claude_stream import RESET

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)


def with_cache_reads(path: Path, scenario: Path) -> Path:
    """``scenario`` with 500 of each assistant message's input tokens read from the cache."""
    lines = []
    for line in scenario.read_text(encoding="utf-8").splitlines():
        message: dict[str, Any] = json.loads(line)
        if message["type"] == "assistant":
            message["message"]["usage"].update(input_tokens=100, cache_read_input_tokens=500)
        if message["type"] == "result":
            message["usage"].update(input_tokens=200, cache_read_input_tokens=1000)
        lines.append(json.dumps(message))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def with_codex_cache_reads(path: Path, scenario: Path) -> Path:
    """``scenario`` with 1,000 of the turn's 1,200 input tokens read from the cache."""
    lines = []
    for line in scenario.read_text(encoding="utf-8").splitlines():
        message: dict[str, Any] = json.loads(line)
        if message["type"] == "turn.completed":
            message["usage"].update(input_tokens=1200, cached_input_tokens=1000)
        lines.append(json.dumps(message))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@dataclass(frozen=True)
class AdapterCase:
    name: str
    make: Callable[[Path, Path, bool], AgentRunner]
    """``make(tmp_path, scenario, hang)``: a runner that plays ``scenario``, then, with
    ``hang``, keeps running for a minute like a stuck agent."""
    fixtures: Path = AGENT_FIXTURES
    shell_tool: str = "Bash"
    """The tool name a denied command is reported under."""
    reports_reset: bool = True
    """Whether the backend reports when a usage limit resets."""
    cached: Callable[[Path, Path], Path] = with_cache_reads

    def scenario(self, name: str) -> Path:
        return self.fixtures / f"{name}.jsonl"


def claude_cli(tmp_path: Path, scenario: Path, hang: bool) -> AgentRunner:
    options = ("--sleep", "60") if hang else ()
    return ClaudeCliRunner(
        claude_cmd=fake_claude_cmd(scenario, tmp_path / "record.json", *options),
        platform="linux",
        which=sandbox_which,
        home=tmp_path / "user-home",
    )


def codex_cli(tmp_path: Path, scenario: Path, hang: bool) -> AgentRunner:
    options = ("--sleep", "60") if hang else ()
    return CodexCliRunner(
        codex_cmd=fake_codex_cmd(scenario, tmp_path / "record.json", *options),
        platform="linux",
        which=sandbox_which,
        home=tmp_path / "user-home",
        system_config=tmp_path / "no-system-config.toml",
        allow_temp_worktree=True,  # pytest's tmp_path is a temp folder
    )


def fake(tmp_path: Path, scenario: Path, hang: bool) -> AgentRunner:
    return FakeRunner(scenario, stall_s=60 if hang else 0)


CODEX = AdapterCase(
    "codex-cli",
    codex_cli,
    fixtures=CODEX_FIXTURES,
    shell_tool="command_execution",
    reports_reset=False,
    cached=with_codex_cache_reads,
)
ADAPTERS = [
    pytest.param(AdapterCase("claude-code-cli", claude_cli), marks=pytest.mark.integration),
    pytest.param(CODEX, marks=pytest.mark.integration),
    pytest.param(AdapterCase("fake", fake)),
]


def run(
    runner: AgentRunner,
    policy: AgentPolicy,
    budget: Budget = BUDGET,
    on_event: Callable[[AgentEvent], None] | None = None,
    cancel: threading.Event | None = None,
) -> tuple[RunResult, list[AgentEvent]]:
    events: list[AgentEvent] = []

    def record(event: AgentEvent) -> None:
        events.append(event)
        if on_event is not None:
            on_event(event)

    result = runner.run(
        AGENT_PROMPT, policy, budget, on_event=record, cancel=cancel or threading.Event()
    )
    return result, events


@pytest.fixture(params=ADAPTERS, ids=lambda case: case.name)
def adapter(request: pytest.FixtureRequest) -> AdapterCase:
    case: AdapterCase = request.param
    return case


def test_a_run_that_creates_a_file(
    adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy
) -> None:
    success = adapter.scenario("success_writes_file")
    result, events = run(adapter.make(tmp_path, success, False), policy)
    assert result.outcome is Outcome.COMPLETED
    assert result.files_changed == ("hello.txt",)
    assert FileEdit(path="hello.txt") in events
    assert isinstance(events[0], Started)


def test_a_denied_command_is_reported_and_logged(
    adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy, caplog: pytest.LogCaptureFixture
) -> None:
    scenario = adapter.scenario("permission_denied")
    result, events = run(adapter.make(tmp_path, scenario, False), policy)
    denied = [event for event in events if isinstance(event, PermissionDenied)]
    assert [event.tool for event in denied] == [adapter.shell_tool]
    assert result.denials == tuple(denied)
    assert any("python3" in record.getMessage() for record in caplog.records)


def test_a_usage_limit_pauses_with_the_reset_time(
    adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy
) -> None:
    scenario = adapter.scenario("usage_limit")
    result, _ = run(adapter.make(tmp_path, scenario, False), policy)
    reset = RESET if adapter.reports_reset else None
    assert (result.outcome, result.reset_at, result.error) == (Outcome.USAGE_LIMITED, reset, None)


def test_a_timeout(adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy) -> None:
    budget = Budget(max_turns=30, max_usd=None, max_tokens=None, timeout_s=1)
    result, _ = run(
        adapter.make(tmp_path, adapter.scenario("success_writes_file"), True), policy, budget
    )
    assert result.outcome is Outcome.TIMED_OUT
    assert result.files_changed == ("hello.txt",)


def test_a_cancel(adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy) -> None:
    cancel = threading.Event()

    def on_event(event: AgentEvent) -> None:
        if isinstance(event, Started):
            cancel.set()

    scenario = adapter.scenario("success_writes_file")
    result, _ = run(
        adapter.make(tmp_path, scenario, True), policy, on_event=on_event, cancel=cancel
    )
    assert (result.outcome, result.error) == (Outcome.CANCELLED, None)


def test_usage_is_reported_and_weighted(
    adapter: AdapterCase, tmp_path: Path, policy: AgentPolicy
) -> None:
    scenario = adapter.cached(tmp_path / "cached.jsonl", adapter.scenario("success_writes_file"))
    # 1,500 raw tokens but 600 weighted (cache reads count a tenth): the budget holds.
    budget = Budget(max_turns=30, max_usd=None, max_tokens=1000)
    result, events = run(adapter.make(tmp_path, scenario, False), policy, budget)
    assert result.outcome is Outcome.COMPLETED
    usage = [event for event in events if isinstance(event, Usage)]
    assert sum(event.cache_read_tokens for event in usage) == 1000
    assert (result.input_tokens, result.output_tokens, result.cache_read_tokens) == (
        1200,
        300,
        1000,
    )
    assert result.weighted_tokens == 200 + 300 + 100

    # Over a smaller budget, the weighted count stops the run.
    budget = Budget(max_turns=30, max_usd=None, max_tokens=500)
    result, _ = run(adapter.make(tmp_path, scenario, True), policy, budget)
    assert result.outcome is Outcome.BUDGET_EXHAUSTED
