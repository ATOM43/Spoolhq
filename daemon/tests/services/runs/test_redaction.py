"""Stored run data is redacted: artifacts and transcript lines on write, and a value the
scan found later in that attempt's files and event rows, events staying append-only."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from spoolhq.services.runs import (
    ArtifactName,
    Attempt,
    AttemptKind,
    EventKind,
    RunLog,
    append_transcript,
    attempt_dir,
    redact_attempt,
    state_db_path,
    write_artifact,
)
from tests.conftest import FixedClock

KEY = "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"
RANDOM = "q8Zr2Lx0Vb7Nw4Kp1Ts9Hd3Fy6Jm5Gc0Ua"
HIDDEN = "[redacted: high-entropy string]"


@pytest.fixture
def run_log(workspace: Path, clock: FixedClock) -> Iterator[RunLog]:
    with RunLog(workspace, clock=clock, daemon_instance="A") as log:
        yield log


@pytest.fixture
def attempt(run_log: RunLog) -> Attempt:
    return run_log.start_attempt(run_log.start_run("T04").id, AttemptKind.INITIAL)


def test_diff_and_transcript_are_redacted_on_write(attempt: Attempt) -> None:
    diff = write_artifact(attempt, ArtifactName.DIFF, f'+API = "{KEY}"\n')
    line = append_transcript(attempt, {"type": "assistant", "text": f"first\n{KEY}"})
    assert diff.read_text(encoding="utf-8") == '+API = "[redacted: Anthropic key]"\n'
    stored = line.read_text(encoding="utf-8")
    assert KEY not in stored
    assert json.loads(stored)["text"] == "first\n[redacted: Anthropic key]"


def test_a_json_artifact_is_redacted_value_by_value(attempt: Attempt) -> None:
    clean = '{\n  "a": 1\n}'
    assert write_artifact(attempt, ArtifactName.GATES, clean).read_text("utf-8") == clean
    leaky = json.dumps({"excerpt": f"got\n{KEY}"})
    stored = write_artifact(attempt, ArtifactName.GATES, leaky).read_text("utf-8")
    assert json.loads(stored) == {"excerpt": "got\n[redacted: Anthropic key]"}


def test_a_found_value_is_redacted_in_the_attempts_files_and_events(
    run_log: RunLog, attempt: Attempt, workspace: Path
) -> None:
    other = run_log.start_attempt(attempt.run_id, AttemptKind.GATE_RETRY)
    write_artifact(attempt, ArtifactName.DIFF, f'+blob = "{RANDOM}"\r\n')
    append_transcript(attempt, {"input": {"content": f'blob = "{RANDOM}"\n'}})
    (attempt_dir(workspace, attempt) / "test.log").write_text(f"saw {RANDOM}", "utf-8")
    run_log.append_event(attempt.run_id, EventKind.AGENT_MESSAGE, {"text": RANDOM}, attempt.id)
    summary = json.dumps({"content": f'"{RANDOM}"'})
    run_log.append_event(
        attempt.run_id, EventKind.AGENT_TOOL_CALL, {"input_summary": summary}, attempt.id
    )
    run_log.append_event(attempt.run_id, EventKind.AGENT_MESSAGE, {"text": RANDOM}, other.id)

    assert redact_attempt(run_log, attempt, {RANDOM}) == 5

    folder = attempt_dir(workspace, attempt)
    assert (folder / "diff.patch").read_bytes() == f'+blob = "{HIDDEN}"\r\n'.encode()
    for path in folder.iterdir():
        assert RANDOM not in path.read_text(encoding="utf-8")
    events = {e.id: e for e in run_log.events_since(0)}
    mine = [e for e in events.values() if e.attempt_id == attempt.id]
    assert all(RANDOM not in json.dumps(e.payload) for e in mine)
    assert json.loads(mine[-1].payload["input_summary"]) == {"content": f'"{HIDDEN}"'}
    # Only that attempt is rewritten.
    assert {"text": RANDOM} in [e.payload for e in events.values() if e.attempt_id == other.id]


def test_events_stay_append_only_after_a_redaction(
    run_log: RunLog, attempt: Attempt, workspace: Path
) -> None:
    run_log.append_event(attempt.run_id, EventKind.AGENT_MESSAGE, {"text": RANDOM}, attempt.id)
    redact_attempt(run_log, attempt, {RANDOM})
    assert redact_attempt(run_log, attempt, set()) == 0
    conn = sqlite3.connect(state_db_path(workspace))
    try:
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("UPDATE events SET kind = 'log'")
    finally:
        conn.close()
