"""FakeRunner: recorded transcripts behind the AgentRunner interface."""

import json
import threading
from pathlib import Path

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentRunner,
    Budget,
    FakeRunner,
    FileEdit,
    Outcome,
)
from tests.conftest import AGENT_FIXTURES

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)
SUCCESS = AGENT_FIXTURES / "success_writes_file.jsonl"


def test_replay_writes_the_file(worktree: Path, policy: AgentPolicy) -> None:
    events: list[AgentEvent] = []
    raw: list[dict[str, object]] = []
    runner: AgentRunner = FakeRunner(SUCCESS)
    result = runner.run(
        "say hello", policy, BUDGET, on_event=events.append, on_raw=raw.append,
        cancel=threading.Event(),
    )  # fmt: skip
    assert (worktree / "hello.txt").read_bytes() == b"hello from spoolhq\n"
    assert result.outcome is Outcome.COMPLETED
    assert result.files_changed == ("hello.txt",)
    # The version the transcript was recorded with.
    assert (result.backend, result.backend_version) == ("fake", "2.1.302")
    assert FileEdit(path="hello.txt") in events
    assert len(raw) == len(SUCCESS.read_text(encoding="utf-8").splitlines())


def test_writes_outside_the_worktree_are_skipped(
    tmp_path: Path, worktree: Path, policy: AgentPolicy
) -> None:
    transcript = tmp_path / "escape.jsonl"
    text = SUCCESS.read_text(encoding="utf-8").replace('"hello.txt"', '"../escape.txt"', 1)
    transcript.write_text(text, encoding="utf-8")
    result = FakeRunner(transcript).run(
        "x", policy, BUDGET, on_event=lambda e: None, cancel=threading.Event()
    )
    assert not (tmp_path / "escape.txt").exists()
    assert result.files_changed == ()


def test_detect() -> None:
    info = FakeRunner(SUCCESS).detect()
    assert (info.installed, info.logged_in, info.billing) == (True, True, "subscription")
    assert info.policy_enforceable and info.usable


def test_cancel(worktree: Path, policy: AgentPolicy) -> None:
    cancel = threading.Event()
    cancel.set()
    result = FakeRunner(SUCCESS).run("x", policy, BUDGET, on_event=lambda e: None, cancel=cancel)
    assert result.outcome is Outcome.CANCELLED
    assert not (worktree / "hello.txt").exists()


def test_token_budget(policy: AgentPolicy) -> None:
    budget = Budget(max_turns=30, max_usd=None, max_tokens=100)
    result = FakeRunner(SUCCESS).run(
        "x", policy, budget, on_event=lambda e: None, cancel=threading.Event()
    )
    assert result.outcome is Outcome.BUDGET_EXHAUSTED


def test_policy_violation(policy: AgentPolicy) -> None:
    result = FakeRunner(AGENT_FIXTURES / "extra_tool_in_init.jsonl").run(
        "x", policy, BUDGET, on_event=lambda e: None, cancel=threading.Event()
    )
    assert result.outcome is Outcome.ERROR
    assert result.error is not None and result.error.startswith("policy not enforced:")


def test_replay_of_the_recorded_real_run(
    tmp_path: Path, worktree: Path, policy: AgentPolicy
) -> None:
    # Recorded by test_real_run.py with SPOOLHQ_RECORD=1; paths were anonymised.
    recorded = AGENT_FIXTURES / "recorded" / "real_run.jsonl"
    transcript = tmp_path / "real_run.jsonl"
    escaped = json.dumps(str(worktree))[1:-1]
    transcript.write_text(
        recorded.read_text(encoding="utf-8").replace("<worktree>", escaped), encoding="utf-8"
    )
    events: list[AgentEvent] = []
    result = FakeRunner(transcript).run(
        "x", policy, BUDGET, on_event=events.append, cancel=threading.Event()
    )
    assert result.outcome is Outcome.COMPLETED
    assert (worktree / "hello.txt").read_text(encoding="utf-8") == "hello from spoolhq"
    assert result.files_changed == ("hello.txt",)
    assert [denial.tool for denial in result.denials] == ["Bash"]
    assert "python3" in result.denials[0].input_summary
    assert result.input_tokens > 0 and result.output_tokens > 0
