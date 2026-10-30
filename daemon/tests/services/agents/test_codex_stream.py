"""CodexStreamParser: ``codex exec --json`` events to SpoolHQ events and a RunResult."""

import json
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentEvent,
    CodexStreamParser,
    FileEdit,
    Message,
    Outcome,
    PermissionDenied,
    PolicyViolation,
    RunResult,
    Started,
    ToolCall,
    Usage,
)
from tests.conftest import CODEX_FIXTURES


def feed(
    worktree: Path, lines: list[dict[str, Any]], read_only: bool = False
) -> tuple[list[AgentEvent], RunResult]:
    parser = CodexStreamParser(worktree, read_only=read_only, model="m", backend_version="0.166.0")
    events = [event for line in lines for event in parser.feed(line)]
    return events, parser.finish()


def fixture(name: str) -> list[dict[str, Any]]:
    path = CODEX_FIXTURES / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def item(kind: str = "item.completed", **fields: Any) -> dict[str, Any]:
    return {"type": kind, "item": {"id": "i1", **fields}}


def done(**usage: int) -> dict[str, Any]:
    return {"type": "turn.completed", "usage": usage}


START = {"type": "thread.started", "thread_id": "t"}


def test_a_run_that_writes_a_file(worktree: Path) -> None:
    events, result = feed(worktree, fixture("success_writes_file"))
    assert events == [
        Started(model="m", tools=(), backend_version="0.166.0"),
        ToolCall(id="item_1", name="command_execution", input_summary='"bash -lc ls"'),
        ToolCall(
            id="item_2",
            name="file_change",
            input_summary='[{"kind": "add", "path": "hello.txt"}]',
        ),
        FileEdit(path="hello.txt"),
        Message(text="Created hello.txt.\n<progress>Added hello.txt.</progress>"),
        Usage(input_tokens=1200, output_tokens=300, cache_read_tokens=0, cache_creation_tokens=0),
    ]
    assert result.outcome is Outcome.COMPLETED
    assert result.summary.endswith("<progress>Added hello.txt.</progress>")
    assert result.files_changed == ("hello.txt",)
    assert (result.input_tokens, result.output_tokens, result.cost_micro_usd) == (1200, 300, None)
    assert (result.backend, result.backend_version, result.model) == ("codex-cli", "0.166.0", "m")
    assert (result.num_turns, result.error, result.debug) == (3, None, {"unknown_events": 0})


def test_usage_with_cached_tokens_is_weighted(worktree: Path) -> None:
    usage = done(
        input_tokens=1200, cached_input_tokens=1000, cache_write_input_tokens=50, output_tokens=300
    )
    events, result = feed(worktree, [START, usage, usage])
    assert events[1:] == [Usage(1200, 300, 1000, 50)] * 2
    assert (result.input_tokens, result.output_tokens, result.cache_read_tokens) == (
        2400,
        600,
        2000,
    )
    # Cached input counts a tenth: 400 fresh + 600 output + 200.
    assert result.weighted_tokens == 1200


def test_paths_inside_and_outside_the_worktree(
    worktree: Path, caplog: pytest.LogCaptureFixture
) -> None:
    changes = [
        {"path": str(worktree / "src" / "a.py"), "kind": "update"},
        {"path": "../outside.py", "kind": "add"},
        {"path": "b.py", "kind": "delete"},
    ]
    events, result = feed(
        worktree, [START, item(type="file_change", changes=changes, status="completed"), done()]
    )
    assert [e.path for e in events if isinstance(e, FileEdit)] == ["src/a.py", "b.py"]
    assert result.files_changed == ("b.py", "src/a.py")
    assert any("outside the worktree" in record.getMessage() for record in caplog.records)


def test_a_failed_patch_changes_nothing(worktree: Path) -> None:
    change = item(type="file_change", changes=[{"path": "a.py", "kind": "add"}], status="failed")
    events, result = feed(worktree, [START, change, done()])
    assert not [e for e in events if isinstance(e, FileEdit)]
    assert result.files_changed == ()


def test_a_sandbox_denial_is_reported_and_logged(
    worktree: Path, caplog: pytest.LogCaptureFixture
) -> None:
    events, result = feed(worktree, fixture("permission_denied"))
    [denied] = [event for event in events if isinstance(event, PermissionDenied)]
    assert denied.tool == "command_execution"
    assert "python3" in denied.input_summary
    assert denied.reason == "sandbox: OSError: [Errno 30] Read-only file system: '../outside.txt'"
    assert result.denials == (denied,)
    assert result.outcome is Outcome.COMPLETED
    assert any("python3" in record.getMessage() for record in caplog.records)


def test_a_failing_command_is_not_a_denial(worktree: Path) -> None:
    started = item(
        "item.started", type="command_execution", command="just test", status="in_progress"
    )
    failed = item(
        type="command_execution",
        command="just test",
        aggregated_output="1 failed\n",
        exit_code=1,
        status="failed",
    )
    events, result = feed(worktree, [START, started, failed, done()])
    assert [e.kind for e in events] == ["started", "tool_call"]  # one tool call, no denial
    assert result.denials == ()


def test_a_usage_limit_pauses_without_a_reset_time(worktree: Path) -> None:
    _, result = feed(worktree, fixture("usage_limit"))
    assert (result.outcome, result.reset_at, result.error) == (Outcome.USAGE_LIMITED, None, None)


def test_an_error(worktree: Path) -> None:
    _, result = feed(worktree, fixture("error"))
    assert (result.outcome, result.error) == (
        Outcome.ERROR,
        "stream disconnected before completion",
    )
    _, ended = feed(worktree, [START])
    assert (ended.outcome, ended.error) == (
        Outcome.ERROR,
        "Codex ended without completing its turn",
    )
    _, bare = feed(worktree, [START, {"type": "turn.failed"}])
    assert bare.error == "the turn failed"


def test_a_completed_turn_wins_over_earlier_errors(worktree: Path) -> None:
    retry = {"type": "error", "message": "Reconnecting... 1/5"}
    _, result = feed(worktree, [START, retry, done(input_tokens=1)])
    assert result.outcome is Outcome.COMPLETED


@pytest.mark.parametrize("kind", ["web_search", "mcp_tool_call"])
def test_turned_off_tools_are_a_policy_violation(worktree: Path, kind: str) -> None:
    parser = CodexStreamParser(worktree, read_only=False)
    parser.feed(START)
    with pytest.raises(PolicyViolation, match=f"Codex used {kind}"):
        parser.feed(item("item.started", type=kind))


def test_a_read_only_run_that_changes_files_is_a_policy_violation(worktree: Path) -> None:
    change = item(type="file_change", changes=[{"path": "a.py", "kind": "add"}], status="completed")
    parser = CodexStreamParser(worktree, read_only=True)
    parser.feed(START)
    with pytest.raises(PolicyViolation, match="read-only"):
        parser.feed(change)


def test_unknown_and_quiet_events_are_ignored(worktree: Path) -> None:
    lines = [
        START,
        START,  # a second thread.started is not a second start
        {"type": "turn.started"},
        {"type": "session.configured"},
        {"type": "item.completed", "item": "not an object"},
        item(type="something_new"),
        item(type="todo_list", items=[]),
        item("item.updated", type="agent_message", text="partial"),
        item("item.started", type="agent_message", text="partial"),
        item(type="agent_message", text=None),
        item(type="error", message="non-fatal"),
        done(input_tokens=5, output_tokens="x"),  # type: ignore[arg-type]
    ]
    events, result = feed(worktree, lines)
    assert events == [Started(model="m", tools=(), backend_version="0.166.0"), Usage(5, 0, 0, 0)]
    assert result.debug == {"unknown_events": 3}
    assert result.outcome is Outcome.COMPLETED


def test_finish_can_override_the_outcome(worktree: Path) -> None:
    parser = CodexStreamParser(worktree, read_only=False)
    parser.feed(START)
    assert not parser.has_result
    result = parser.finish(Outcome.TIMED_OUT)
    assert (result.outcome, result.error) == (Outcome.TIMED_OUT, None)
