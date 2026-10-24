"""ClaudeStreamParser: stream-json messages to events and a RunResult."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    ClaudeStreamParser,
    FileEdit,
    Message,
    Outcome,
    PermissionDenied,
    PolicyViolation,
    RateLimit,
    Started,
    ToolCall,
    Usage,
)
from spoolhq.services.agents.claude_stream import epoch_to_datetime, summarize, usd_to_micro
from spoolhq.services.agents.model import AgentEvent, Billing
from spoolhq.services.context import extract_progress_note
from tests.conftest import AGENT_FIXTURES

RESET = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
INIT: dict[str, Any] = {
    "type": "system",
    "subtype": "init",
    "tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write"],
    "model": "claude-test-model",
    "permissionMode": "dontAsk",
    "claude_code_version": "2.1.302",
}


def load(name: str) -> list[dict[str, Any]]:
    lines = (AGENT_FIXTURES / name).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def replay(parser: ClaudeStreamParser, messages: list[dict[str, Any]]) -> list[AgentEvent]:
    events: list[AgentEvent] = []
    for message in messages:
        events += parser.feed(message)
    return events


def parse(
    worktree: Path, name: str, billing: Billing = "subscription"
) -> tuple[list[AgentEvent], ClaudeStreamParser]:
    parser = ClaudeStreamParser(worktree, billing=billing)
    return replay(parser, load(name)), parser


def assistant(*blocks: dict[str, Any], message_id: str = "m1", **usage: int) -> dict[str, Any]:
    return {
        "type": "assistant",
        "message": {"id": message_id, "content": list(blocks), "usage": usage},
    }


def tool_use(tool_id: str, name: str, **tool_input: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}


def tool_result(tool_id: str, *, is_error: bool = False) -> dict[str, Any]:
    block = {"type": "tool_result", "tool_use_id": tool_id, "content": "ok", "is_error": is_error}
    return {"type": "user", "message": {"content": [block]}}


def result(subtype: str = "success", is_error: bool = False, **fields: Any) -> dict[str, Any]:
    return {"type": "result", "subtype": subtype, "is_error": is_error, **fields}


# --- success ------------------------------------------------------------------------


def test_success_writes_file(worktree: Path) -> None:
    events, parser = parse(worktree, "success_writes_file.jsonl")
    run = parser.finish()
    assert run.outcome is Outcome.COMPLETED
    assert run.files_changed == ("hello.txt",)
    assert (run.input_tokens, run.output_tokens) == (1200, 300)
    assert run.cost_micro_usd is None
    assert run.summary == "Created hello.txt."
    assert run.error is None
    assert run.reset_at is None
    assert run.num_turns == 2
    assert (run.backend, run.backend_version, run.model) == (
        "claude-code-cli",
        "2.1.302",
        "claude-test-model",
    )
    assert [event.kind for event in events] == [
        "started",
        "usage",
        "message",
        "tool_call",
        "file_edit",
        "usage",
        "message",
        "rate_limit",
    ]
    assert events[0] == Started(
        model="claude-test-model",
        tools=("Bash", "Edit", "Glob", "Grep", "Read", "Write"),
        backend_version="2.1.302",
    )
    assert events[3] == ToolCall(
        id="toolu_01",
        name="Write",
        input_summary='{"content": "hello from spoolhq\\n", "file_path": "hello.txt"}',
    )
    assert events[4] == FileEdit(path="hello.txt")


def test_api_billing_reports_cost_in_micro_usd(worktree: Path) -> None:
    _, parser = parse(worktree, "success_writes_file.jsonl", billing="api")
    assert parser.finish().cost_micro_usd == 12300


def test_usage_is_counted_once_per_message_id(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    events = replay(
        parser,
        [
            INIT,
            assistant({"type": "text", "text": "a"}, input_tokens=100, output_tokens=10),
            # The same message again, for its next content block.
            assistant(tool_use("t1", "Read", file_path="x"), input_tokens=100, output_tokens=10),
            assistant(message_id="m2", input_tokens=50, output_tokens=5),
        ],
    )
    assert [event for event in events if isinstance(event, Usage)] == [
        Usage(input_tokens=100, output_tokens=10, cache_read_tokens=0, cache_creation_tokens=0),
        Usage(input_tokens=50, output_tokens=5, cache_read_tokens=0, cache_creation_tokens=0),
    ]
    assert parser.weighted_tokens == 165
    # Without a result message, the totals come from the assistant messages.
    run = parser.finish()
    assert (run.input_tokens, run.output_tokens, run.num_turns) == (150, 15, 2)


def test_cached_tokens_count_as_input(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    usage = {
        "input_tokens": 2,
        "output_tokens": 31,
        "cache_read_input_tokens": 5272,
        "cache_creation_input_tokens": 4220,
    }
    events = replay(parser, [INIT, assistant(**usage), result(usage=usage)])
    assert events[1] == Usage(2, 31, 5272, 4220)
    run = parser.finish()
    assert (run.input_tokens, run.output_tokens) == (2 + 5272 + 4220, 31)


def test_summary_is_cut_to_4000_characters(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, result(result="a" * 1000 + "x" * 4000)])
    assert parser.finish().summary == "[… 1,000 characters cut …]\n" + "x" * 4000


def test_summary_keeps_the_progress_note_at_the_end(worktree: Path) -> None:
    note = "<progress>Added the workspace folder.</progress>"
    text = "Long report. " * 1000
    text = text[: 10_000 - len(note)] + note
    assert len(text) == 10_000
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, result(result=text)])
    assert extract_progress_note(parser.finish().summary) == "Added the workspace folder."


def test_tool_input_summary_is_cut_to_2000_characters(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    events = replay(parser, [INIT, assistant(tool_use("t1", "Bash", command="y" * 3000))])
    call = events[-1]
    assert isinstance(call, ToolCall)
    assert len(call.input_summary) == 2000
    assert summarize({"a": 1}) == '{"a": 1}'


# --- file edits ---------------------------------------------------------------------


def test_edit_outside_the_worktree_is_not_a_file_edit(
    worktree: Path, caplog: pytest.LogCaptureFixture
) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    with caplog.at_level(logging.WARNING, logger="spoolhq.services.agents.claude_stream"):
        events = replay(
            parser,
            [
                INIT,
                assistant(tool_use("t1", "Edit", file_path="../outside.txt", old_string="a")),
                tool_result("t1"),
                assistant(tool_use("t2", "Write", file_path=str(worktree.parent / "x.txt"))),
                tool_result("t2"),
            ],
        )
    assert not [event for event in events if isinstance(event, FileEdit)]
    assert parser.finish().files_changed == ()
    messages = [record.getMessage() for record in caplog.records]
    assert "agent file edit outside the worktree: Edit ../outside.txt" in messages


def test_file_edits_are_sorted_deduplicated_and_relative(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(
        parser,
        [
            INIT,
            assistant(
                tool_use("t1", "Write", file_path=str(worktree / "src" / "b.py"), content=""),
                tool_use("t2", "Edit", file_path="a.py"),
                tool_use("t3", "MultiEdit", file_path="src/b.py"),
                tool_use("t4", "NotebookEdit", notebook_path="nb/x.ipynb"),
                tool_use("t5", "Edit", file_path="failed.py"),
                tool_use("t6", "Read", file_path="read.py"),
                tool_use("t7", "Edit", file_path="."),
            ),
            tool_result("t1"),
            tool_result("t2"),
            tool_result("t3"),
            tool_result("t4"),
            tool_result("t5", is_error=True),
            tool_result("t6"),
            tool_result("t7"),
        ],
    )
    assert parser.finish().files_changed == ("a.py", "nb/x.ipynb", "src/b.py")


# --- denials ------------------------------------------------------------------------


def test_permission_denied_is_an_event_a_denial_and_a_warning(
    worktree: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING):
        events, parser = parse(worktree, "permission_denied.jsonl")
    denials = [event for event in events if isinstance(event, PermissionDenied)]
    expected = PermissionDenied(
        tool="Bash",
        input_summary='{"command": "python3 -c \'print(1)\'", '
        '"description": "Run a Python one-liner"}',
        reason="no approval surface in this session; permission request denied automatically",
    )
    # Reported twice (system message and result), recorded once.
    assert denials == [expected]
    run = parser.finish()
    assert run.denials == (expected,)
    assert run.outcome is Outcome.COMPLETED
    warnings = [record for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "python3" in warnings[0].getMessage()
    assert warnings[0].tool == "Bash"  # type: ignore[attr-defined]


def test_denial_only_in_the_result_is_still_reported(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    denial = {"tool_name": "Bash", "tool_use_id": "t9", "tool_input": {"command": "curl x"}}
    events = replay(parser, [INIT, result(permission_denials=[denial])])
    assert events[1:] == [
        PermissionDenied(
            tool="Bash",
            input_summary='{"command": "curl x"}',
            reason="denied by the permission policy",
        )
    ]


def test_denied_edit_is_not_a_file_edit(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(
        parser,
        [
            INIT,
            assistant(tool_use("t1", "Write", file_path="a.txt", content="x")),
            {"type": "system", "subtype": "permission_denied", "tool_name": "Write",
             "tool_use_id": "t1", "message": "denied"},
            tool_result("t1"),
        ],
    )  # fmt: skip
    run = parser.finish()
    assert run.files_changed == ()
    assert run.denials[0].reason == "denied"


# --- outcomes -----------------------------------------------------------------------


def test_usage_limit(worktree: Path) -> None:
    events, parser = parse(worktree, "usage_limit.jsonl")
    run = parser.finish()
    assert run.outcome is Outcome.USAGE_LIMITED
    assert run.reset_at == RESET
    assert run.error is None
    assert RateLimit(status="rejected", reset_at=RESET) in events


def test_usage_limit_from_the_result_text_alone(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, result(is_error=True, result="Claude AI usage limit reached|1792317600")])
    run = parser.finish()
    assert (run.outcome, run.reset_at, run.error) == (Outcome.USAGE_LIMITED, RESET, None)


def test_usage_limit_text_without_a_time(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, result("error_during_execution", True, errors=["5-hour USAGE LIMIT"])])
    run = parser.finish()
    assert (run.outcome, run.reset_at) == (Outcome.USAGE_LIMITED, None)


def test_assistant_rate_limit_error_without_later_success(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    limited = {**assistant(), "error": "rate_limit"}
    replay(parser, [INIT, limited, result("error_during_execution", True, errors=["stopped"])])
    assert parser.finish().outcome is Outcome.USAGE_LIMITED

    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, limited, result(result="done after a retry")])
    assert parser.finish().outcome is Outcome.COMPLETED


def test_rejected_rate_limit_without_a_result(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    rejected = {
        "type": "rate_limit_event",
        "rate_limit_info": {"status": "rejected", "resetsAt": 1792317600000},
    }
    replay(parser, [INIT, rejected])
    run = parser.finish()
    assert (run.outcome, run.reset_at) == (Outcome.USAGE_LIMITED, RESET)


def test_api_retry_on_rate_limit_is_reported(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    retry = {"type": "system", "subtype": "api_retry", "error": "rate_limit", "attempt": 1}
    assert parser.feed(retry) == [RateLimit(status="retrying", reset_at=None)]
    assert parser.feed({"type": "system", "subtype": "api_retry", "error": "overloaded"}) == []


def test_max_turns(worktree: Path) -> None:
    _, parser = parse(worktree, "max_turns.jsonl")
    run = parser.finish()
    assert (run.outcome, run.error, run.num_turns) == (Outcome.MAX_TURNS, None, 2)


def test_budget_exhausted(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="api")
    replay(parser, [INIT, result("error_max_budget_usd", True, total_cost_usd=1.5)])
    run = parser.finish()
    assert (run.outcome, run.cost_micro_usd) == (Outcome.BUDGET_EXHAUSTED, 1_500_000)


def test_error(worktree: Path) -> None:
    _, parser = parse(worktree, "error.jsonl")
    run = parser.finish()
    assert run.outcome is Outcome.ERROR
    assert run.error == "API Error: 500 Internal server error"


def test_error_text_falls_back_to_the_subtype(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, result("error_during_execution", True)])
    assert parser.finish().error == "error_during_execution"


def test_no_result_is_an_error(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    replay(parser, [INIT, assistant({"type": "text", "text": "hi"})])
    run = parser.finish()
    assert (run.outcome, run.error) == (Outcome.ERROR, "Claude Code ended without a result")


def test_override_outcome(worktree: Path) -> None:
    _, parser = parse(worktree, "success_writes_file.jsonl")
    run = parser.finish(Outcome.CANCELLED)
    assert (run.outcome, run.error, run.files_changed) == (Outcome.CANCELLED, None, ("hello.txt",))


# --- init verification --------------------------------------------------------------


def test_extra_tool_in_init_is_a_policy_violation(worktree: Path) -> None:
    with pytest.raises(PolicyViolation, match=r"tools that were not requested: \['WebFetch'\]"):
        parse(worktree, "extra_tool_in_init.jsonl")


@pytest.mark.parametrize("tool", ["mcp__github__create_issue", "WebSearch", "Task"])
def test_unrequested_tools_are_violations(worktree: Path, tool: str) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    with pytest.raises(PolicyViolation, match=tool):
        parser.feed({**INIT, "tools": [*INIT["tools"], tool]})


def test_forbidden_tools_are_violations_even_if_requested(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription", requested_tools=["WebFetch"])
    with pytest.raises(PolicyViolation, match="WebFetch"):
        parser.feed({**INIT, "tools": ["WebFetch"]})


@pytest.mark.parametrize("mode", ["bypassPermissions", "acceptEdits", "auto", "default", None])
def test_other_permission_modes_are_violations(worktree: Path, mode: str | None) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    with pytest.raises(PolicyViolation, match="expected dontAsk"):
        parser.feed({**INIT, "permissionMode": mode})


def test_accepted_modes_can_be_widened_by_the_adapter(worktree: Path) -> None:
    parser = ClaudeStreamParser(
        worktree, billing="subscription", permission_modes={"dontAsk", "default"}
    )
    assert isinstance(parser.feed({**INIT, "permissionMode": "default"})[0], Started)


def test_acting_before_init_is_a_violation(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    with pytest.raises(PolicyViolation, match="before its init message"):
        parser.feed(assistant({"type": "text", "text": "hi"}))


def test_unknown_events_are_ignored_and_counted(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    events = replay(
        parser,
        [
            {"type": "active_goal", "value": None},
            INIT,
            {"type": "stream_event", "event": {"type": "message_start"}},
            {"type": "system", "subtype": "status", "status": "requesting"},
            {"type": "autocompact_state"},
            assistant({"type": "thinking", "thinking": ""}, {"type": "text", "text": "hi"}),
            {"type": "user", "message": {"content": "plain text"}},
        ],
    )
    assert [event.kind for event in events] == ["started", "message"]
    assert events[1] == Message(text="hi")
    assert parser.finish().debug == {"unknown_events": 2}


# --- helpers ------------------------------------------------------------------------


def test_epoch_conversion() -> None:
    assert epoch_to_datetime(1792317600) == RESET
    assert epoch_to_datetime(1792317600000) == RESET
    assert epoch_to_datetime("1792317600") == RESET
    assert epoch_to_datetime(None) is None
    assert epoch_to_datetime(True) is None
    assert epoch_to_datetime("soon") is None
    assert epoch_to_datetime(10**30) is None


def test_usd_conversion_is_exact() -> None:
    assert usd_to_micro(0.0123) == 12300
    assert usd_to_micro(0.1 + 0.2) == 300000
    assert usd_to_micro(0.0000005) == 1
    assert usd_to_micro(None) is None
    assert usd_to_micro(False) is None
    assert usd_to_micro("abc") is None


def test_exact_tools_requires_every_requested_tool(worktree: Path) -> None:
    parser = ClaudeStreamParser(
        worktree, billing="subscription", requested_tools=["Read", "Glob", "Grep"], exact_tools=True
    )
    init: dict[str, object] = {"type": "system", "subtype": "init", "permissionMode": "dontAsk"}
    init["tools"] = ["Read", "Glob"]
    with pytest.raises(PolicyViolation, match=r"missing requested tools: \['Grep'\]"):
        parser.feed(init)
    parser.feed({**init, "tools": ["Grep", "Read", "Glob"]})


# --- weighted tokens ----------------------------------------------------------------

# T29's implementer, per call: (input, output, cache read, cache write), from its transcript.
T29_CALLS = [
    (2, 5, 5379, 25202), (2, 16, 30581, 740), (2, 9, 31321, 5463), (2, 5, 36784, 4454),
    (2, 16, 41238, 850), (2, 8, 42088, 7669), (2, 16, 49757, 2065), (2, 8, 51822, 1179),
    (2, 8, 53001, 1840), (2, 37, 54841, 1877), (2, 38, 56718, 504), (2, 24, 57222, 1905),
    (2, 5, 59127, 493), (2, 3, 59620, 1151), (2, 16, 60771, 1027), (2, 6, 61798, 618),
    (2, 16, 62416, 1153), (2, 16, 63569, 1086), (2, 2, 64655, 976), (2, 2, 65631, 1371),
    (2, 17, 67002, 475), (2, 3, 67477, 589), (2, 8, 68066, 2022), (2, 16, 70088, 691),
    (2, 7, 70779, 4870), (2, 10, 75649, 960), (2, 9, 76609, 3964), (2, 3, 80573, 3572),
    (2, 16, 84145, 1709), (2, 16, 85854, 449), (2, 16, 86303, 812), (2, 8, 87115, 1136),
    (2, 8, 88251, 642), (2, 6, 88893, 1072),
]  # fmt: skip


def test_t29_weighs_cache_reads_at_a_tenth(worktree: Path) -> None:
    parser = ClaudeStreamParser(worktree, billing="subscription")
    calls = [
        assistant(
            message_id=f"m{n}",
            input_tokens=i,
            output_tokens=o,
            cache_read_input_tokens=cr,
            cache_creation_input_tokens=cc,
        )
        for n, (i, o, cr, cc) in enumerate(T29_CALLS)
    ]
    replay(parser, [INIT, *calls])
    # About 2.2M raw, but 2.1M of it is cache reads: about 300k weighted.
    assert parser.input_tokens + parser.output_tokens == 2_190_196
    assert parser.cache_read_tokens == 2_105_143
    assert parser.weighted_tokens == 68 + 399 + 84_586 + 210_514 == 295_567

    # The result's usage (T29's real totals) wins over the per-call sums.
    final = {
        "input_tokens": 68,
        "output_tokens": 16221,
        "cache_read_input_tokens": 2_105_143,
        "cache_creation_input_tokens": 84_586,
    }
    replay(parser, [result(usage=final)])
    run = parser.finish()
    assert (run.input_tokens, run.output_tokens, run.cache_read_tokens) == (
        2_189_797,
        16_221,
        2_105_143,
    )
    assert run.weighted_tokens == 311_389
