"""Step events and the implementer's live transcript in the run log."""

from datetime import UTC, datetime

import pytest

from spoolhq.services.agents import (
    PermissionDenied,
    RateLimit,
    Started,
    StreamWarning,
    ToolResult,
)
from spoolhq.services.runloop import LocalIntegrator, RunLoop
from spoolhq.services.runloop.transcript import Recorder, event_payload
from spoolhq.services.runs import EventKind, RunLog, RunRegistry
from tests.services.runloop.conftest import (
    INIT_TOOLS,
    PASSING,
    LoopFactory,
    ManualClock,
    Transcripts,
    _assistant,
    _init,
    _result,
    failing,
)


def run_once(loop: RunLoop) -> int:
    run = loop.start("demo", "next")
    loop.wait("demo")
    return run.id


def steps(log: RunLog, run_id: int) -> list[tuple[str, str, int]]:
    return [
        (str(e.payload["step"]), str(e.payload["state"]), int(e.payload["attempt"]))
        for e in log.events_since(0, run_id=run_id)
        if e.kind is EventKind.STEP
    ]


def test_a_happy_run_steps_through_every_step_in_order(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry, clock: ManualClock
) -> None:
    loop, _ = make_loop(
        [transcripts.implement()],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )

    run_id = run_once(loop)

    names = ("worktree", "implement", "gates", "review", "policy", "integrate")
    expected = [(name, state, 1) for name in names for state in ("running", "passed")]
    assert steps(registry.get("demo").run_log, run_id) == expected


def test_a_gate_failure_retries_from_implement_with_the_next_attempt(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    loop, _ = make_loop(
        [transcripts.implement(), transcripts.implement()],
        [transcripts.review("approve")],
        gates=[failing("tests/test_a.py::test_a"), PASSING],
    )

    run_id = run_once(loop)

    seen = steps(registry.get("demo").run_log, run_id)
    failed = seen.index(("gates", "failed", 1))
    assert seen[failed + 1] == ("implement", "running", 2)
    assert ("review", "running", 1) not in seen


def test_the_implementer_transcript_is_recorded_on_its_attempt(
    make_loop: LoopFactory, transcripts: Transcripts, registry: RunRegistry
) -> None:
    write = {"file_path": "hello.py", "content": "a = 1\nb = 2\n"}
    answer = {"type": "tool_result", "tool_use_id": "w0", "content": "File created"}
    implementer = transcripts._write(
        [
            _init(INIT_TOOLS),
            _assistant(
                [{"type": "tool_use", "id": "w0", "name": "Write", "input": write}], 1000, "m1"
            ),
            {"type": "user", "message": {"role": "user", "content": [answer]}},
            _result("Done.", 1000),
        ]
    )
    loop, _ = make_loop([implementer], [transcripts.review("approve")])

    run_id = run_once(loop)

    log = registry.get("demo").run_log
    attempt = log.list_attempts(run_id)[0]
    agent = [e for e in log.events_since(0, run_id=run_id) if e.kind.value.startswith("agent.")]
    assert {e.attempt_id for e in agent} == {attempt.id}
    by_kind = {e.kind: e.payload for e in agent}
    assert by_kind[EventKind.AGENT_TOOL_CALL]["name"] == "Write"
    assert by_kind[EventKind.AGENT_FILE_EDIT] == {"path": "hello.py", "added": 2, "removed": None}
    assert by_kind[EventKind.AGENT_TOOL_RESULT] == {
        "id": "w0",
        "text": "File created",
        "lines": 1,
        "is_error": False,
    }
    assert by_kind[EventKind.AGENT_USAGE]["input_tokens"] == 1000


def test_payloads_of_denials_limits_warnings_and_long_results() -> None:
    reset = datetime(2026, 11, 7, 14, 30, tzinfo=UTC)
    assert event_payload(Started("m", (), "1")) is None
    assert event_payload(PermissionDenied("Bash", '{"command": "rm -rf /"}', "no")) == (
        EventKind.AGENT_DENIED,
        {"tool": "Bash", "input_summary": '{"command": "rm -rf /"}', "reason": "no"},
    )
    assert event_payload(RateLimit("rejected", reset)) == (
        EventKind.AGENT_RATE_LIMIT,
        {"status": "rejected", "reset_at": "2026-11-07T14:30:00+00:00"},
    )
    assert event_payload(StreamWarning("skipped", "{")) == (
        EventKind.AGENT_WARNING,
        {"text": "skipped", "line": "{"},
    )
    long = "\n".join(f"line {n}" for n in range(450))
    found = event_payload(ToolResult("t1", long, is_error=False))
    assert found is not None
    kind, payload = found
    assert kind is EventKind.AGENT_TOOL_RESULT
    assert payload["lines"] == 450
    assert payload["text"].splitlines()[-1] == "line 199"


def test_a_recorder_never_stops_the_run(caplog: pytest.LogCaptureFixture) -> None:
    class Refusing:
        def append_event(self, *_args: object) -> None:
            raise ValueError("too large")

    attempt = type("A", (), {"run_id": 1, "id": 2})()
    Recorder(Refusing(), attempt)(StreamWarning("x", "y"))  # type: ignore[arg-type]
    Recorder(Refusing(), attempt)(Started("m", (), "1"))  # type: ignore[arg-type]
    assert "cannot record an agent event" in caplog.text
