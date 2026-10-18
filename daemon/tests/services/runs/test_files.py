"""Attempt files: allowed names, atomic writes, the transcript and finding them again."""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from spoolhq.services.runs import (
    ARTIFACT_NAMES,
    Attempt,
    AttemptKind,
    RunLog,
    append_transcript,
    attempt_files,
    state_db_path,
    write_artifact,
)
from tests.conftest import FixedClock


@pytest.fixture
def run_log(workspace: Path, clock: FixedClock) -> Iterator[RunLog]:
    with RunLog(workspace, clock=clock, daemon_instance="A") as log:
        yield log


@pytest.fixture
def attempt(run_log: RunLog) -> Attempt:
    return run_log.start_attempt(run_log.start_run("T04").id, AttemptKind.INITIAL)


CONTENT = {
    "transcript.jsonl": '{"role":"assistant","text":"hi"}\n',
    "gates.json": '{"lint": "passed"}\n',
    "diff.patch": "--- a/x\n+++ b/x\n@@ -1 +1 @@\n-old\n+new ✓\n",
    "review.json": '{"verdict": "approved"}\n',
}


@pytest.mark.parametrize("name", sorted(ARTIFACT_NAMES))
def test_each_allowed_name_writes_and_reads_back(attempt: Attempt, name: str) -> None:
    path = write_artifact(attempt, name, CONTENT[name])
    assert path.read_bytes() == CONTENT[name].encode("utf-8")
    write_artifact(attempt, name, b"\x00\x01 bytes")
    assert path.read_bytes() == b"\x00\x01 bytes"
    assert list(path.parent.glob("*.tmp")) == []


@pytest.mark.parametrize("name", ["notes.txt", "../x", "a/b", "a\\b", "", ".."])
def test_other_names_are_refused(attempt: Attempt, workspace: Path, name: str) -> None:
    with pytest.raises(ValueError, match="invalid attempt file name"):
        write_artifact(attempt, name, "x")
    assert list((workspace / attempt.dir).iterdir()) == []


def test_write_leaves_no_temp_file(attempt: Attempt, workspace: Path) -> None:
    write_artifact(attempt, "diff.patch", "x" * 100_000)
    write_artifact(attempt, "diff.patch", "shorter")
    folder = workspace / attempt.dir
    assert sorted(p.name for p in folder.iterdir()) == ["diff.patch"]
    assert list(folder.glob("*.tmp")) == []
    assert (folder / "diff.patch").read_text(encoding="utf-8") == "shorter"


def test_failed_write_leaves_no_temp_file(
    attempt: Attempt, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_replace(src: str, dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr("spoolhq.services.runs.files.os.replace", broken_replace)
    with pytest.raises(OSError, match="disk full"):
        write_artifact(attempt, "gates.json", "{}")
    assert list((workspace / attempt.dir).iterdir()) == []


def test_append_transcript_writes_json_lines(attempt: Attempt) -> None:
    append_transcript(attempt, {"role": "user", "text": "fix T04"})
    path = append_transcript(attempt, {"role": "assistant", "text": "done ✓"})
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line) for line in lines] == [
        {"role": "user", "text": "fix T04"},
        {"role": "assistant", "text": "done ✓"},
    ]


@pytest.mark.parametrize("record", [{"x": {1}}, ["list"], "text"])
def test_append_transcript_refuses_non_json(attempt: Attempt, record: object) -> None:
    with pytest.raises(ValueError, match="transcript record"):
        append_transcript(attempt, record)  # type: ignore[arg-type]


def test_every_attempt_finds_its_files_from_its_row(run_log: RunLog, workspace: Path) -> None:
    run_a = run_log.start_run("T04")
    run_b = run_log.start_run("T05")
    created = [
        run_log.start_attempt(run_a.id, AttemptKind.INITIAL),
        run_log.start_attempt(run_a.id, AttemptKind.REVIEW_RETRY),
        run_log.start_attempt(run_b.id, AttemptKind.INITIAL),
    ]
    for attempt in created:
        for name, text in CONTENT.items():
            write_artifact(attempt, name, text)

    runs_root = (workspace / "runs").resolve()
    rows = run_log.list_attempts(run_a.id) + run_log.list_attempts(run_b.id)
    assert [a.id for a in rows] == [a.id for a in created]
    for attempt in rows:
        files = attempt_files(workspace, attempt)
        assert sorted(files) == sorted(ARTIFACT_NAMES)
        for name, path in files.items():
            assert path.is_file()
            assert path.is_relative_to(runs_root)
            assert path.read_text(encoding="utf-8") == CONTENT[name]


def test_attempt_files_lists_only_existing_files(attempt: Attempt, workspace: Path) -> None:
    assert attempt_files(workspace, attempt) == {}
    write_artifact(attempt, "gates.json", "{}")
    assert list(attempt_files(workspace, attempt)) == ["gates.json"]


@pytest.mark.parametrize("bad_dir", ["../../etc", "runs/../..", "runs", "tickets", "/etc"])
def test_dir_outside_runs_is_refused(
    run_log: RunLog, attempt: Attempt, workspace: Path, bad_dir: str
) -> None:
    conn = sqlite3.connect(state_db_path(workspace))
    with conn:
        conn.execute("UPDATE attempts SET dir = ? WHERE id = ?", (bad_dir, attempt.id))
    conn.close()

    edited = run_log.get_attempt(attempt.id)
    assert edited.dir == bad_dir
    with pytest.raises(ValueError, match="outside runs/"):
        attempt_files(workspace, edited)
    with pytest.raises(ValueError, match="outside runs/"):
        write_artifact(edited, "gates.json", "{}")
    with pytest.raises(ValueError, match="outside runs/"):
        append_transcript(edited, {"x": 1})
