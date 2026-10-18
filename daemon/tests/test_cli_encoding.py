"""The CLI writes UTF-8 even when the console code page cannot encode its arrows."""

import io
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from spoolhq.cli import main
from spoolhq.cli.main import _force_utf8_streams

TICKET = """\
---
id: {id}
title: Ticket {id}
phase: 0
depends_on: [{deps}]
status: {status}
estimate_h: 1
---

## Done when
- [ ] It works
"""


def write(tickets: Path, ticket_id: str, deps: str = "", status: str = "ready") -> None:
    path = tickets / f"{ticket_id}-x.md"
    path.write_text(TICKET.format(id=ticket_id, deps=deps, status=status), encoding="utf-8")


def make_project(projects_dir: Path, name: str = "demo") -> Path:
    tickets = projects_dir / name / "tickets"
    tickets.mkdir(parents=True)
    return tickets


def run_spool_cp1252(*args: str) -> subprocess.CompletedProcess[bytes]:
    """Run the real CLI with a cp1252 output encoding and both streams piped, as on Windows."""
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONUTF8": "0"}
    return subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-m", "spoolhq", *args],
        env=env,
        capture_output=True,
        check=False,
        timeout=60,
    )


# Real CLI in a subprocess -------------------------------------------------------------


@pytest.mark.integration
def test_plan_check_writes_utf8_arrows_under_cp1252(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01", deps="T02")
    write(tickets, "T02", deps="T01")

    result = run_spool_cp1252("plan", "check", "demo")

    stderr = result.stderr.decode("utf-8")
    assert "UnicodeEncodeError" not in stderr
    assert result.returncode == 1, stderr
    assert "T01 → T02 → T01" in result.stdout.decode("utf-8")


@pytest.mark.integration
def test_set_status_refusal_writes_utf8_arrow_under_cp1252(projects_dir: Path) -> None:
    tickets = make_project(projects_dir)
    write(tickets, "T01", status="blocked")

    result = run_spool_cp1252("tickets", "set-status", "demo", "T01", "done")

    stderr = result.stderr.decode("utf-8")
    assert "UnicodeEncodeError" not in stderr
    assert result.returncode == 1, stderr
    assert "blocked → done" in stderr


# _force_utf8_streams ------------------------------------------------------------------


class FakeStream:
    """A stream with a spy in place of ``reconfigure``."""

    def __init__(self, encoding: str) -> None:
        self.encoding = encoding
        self.errors = "strict"
        self.reconfigure = MagicMock()


def test_cp1252_stream_becomes_utf8_and_keeps_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    stderr = io.TextIOWrapper(io.BytesIO(), encoding="cp1252", errors="backslashreplace")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    _force_utf8_streams()

    assert stdout.encoding == "utf-8"
    assert stderr.encoding == "utf-8"
    assert stdout.errors == "strict"
    assert stderr.errors == "backslashreplace"
    stdout.write("blocked → done")
    stdout.flush()
    assert stdout.buffer.getvalue().decode("utf-8") == "blocked → done"  # type: ignore[attr-defined]


def test_streams_without_reconfigure_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdout", object())
    monkeypatch.setattr(sys, "stderr", None)

    _force_utf8_streams()


@pytest.mark.parametrize("encoding", ["utf-8", "UTF-8", "utf8", "UTF8", "utf_8"])
def test_utf8_streams_are_not_reconfigured(monkeypatch: pytest.MonkeyPatch, encoding: str) -> None:
    stdout, stderr = FakeStream(encoding), FakeStream(encoding)
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    _force_utf8_streams()

    stdout.reconfigure.assert_not_called()
    stderr.reconfigure.assert_not_called()


def test_reconfigure_failure_is_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = FakeStream("cp1252")
    stdout.reconfigure.side_effect = ValueError("I/O operation on closed file.")
    stderr = FakeStream("cp1252")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)

    _force_utf8_streams()

    stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="strict")


def test_main_forces_utf8_before_running_the_app(monkeypatch: pytest.MonkeyPatch) -> None:
    stdout = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "argv", ["spool", "--help"])

    with pytest.raises(SystemExit) as exit_info:
        main()

    assert exit_info.value.code == 0
    assert stdout.encoding == "utf-8"
    stdout.flush()
    assert "SpoolHQ" in stdout.buffer.getvalue().decode("utf-8")  # type: ignore[attr-defined]
