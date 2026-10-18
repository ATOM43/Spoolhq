"""Running one command: the output cap, timeouts and the process tree."""

import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest

from spoolhq.services.gates.command import gate_env
from spoolhq.services.gates.process import ProcessResult, run_process
from tests.conftest import fake_tool_cmd

pytestmark = pytest.mark.integration


def run(
    tmp_path: Path, *args: str, timeout_s: float = 30, cap_bytes: int = 20_000_000
) -> ProcessResult:
    return run_process(
        shlex.split(fake_tool_cmd(*args)),
        cwd=tmp_path,
        env=gate_env(os.environ, platform=sys.platform),
        timeout_s=timeout_s,
        log_path=tmp_path / "out.log",
        cap_bytes=cap_bytes,
    )


def alive(pid: int) -> bool:
    if sys.platform == "win32":
        listing = subprocess.run(  # noqa: S603 - fixed argument list
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
        return str(pid) in listing.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    status = Path(f"/proc/{pid}/status")
    # A killed child nobody has reaped yet is gone for our purposes.
    return not (status.exists() and "\nState:\tZ" in status.read_text(encoding="utf-8"))


def test_output_cap_cuts_the_log_and_drains_the_process(tmp_path: Path) -> None:
    result = run(tmp_path, "flood", cap_bytes=10_000)

    assert result.exit_code == 1
    assert result.timed_out is False
    assert result.output_truncated is True
    assert result.output_lines == 50_002
    log = (tmp_path / "out.log").read_text(encoding="utf-8")
    assert log.endswith("\n[output cut at 0.01 MB]\n")
    assert len(log.encode()) <= 10_000 + 30


def test_timeout_stops_the_whole_process_tree(tmp_path: Path) -> None:
    pid_file = tmp_path / "child.pid"
    start = time.monotonic()

    result = run(tmp_path, "sleep-with-child", str(pid_file), timeout_s=1)

    assert time.monotonic() - start < 10
    assert result.timed_out is True
    assert result.exit_code is None
    child = int(pid_file.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while alive(child) and time.monotonic() < deadline:
        time.sleep(0.1)
    assert not alive(child)


def test_invalid_utf8_and_crlf_are_cleaned_in_the_log(tmp_path: Path) -> None:
    result = run(tmp_path, "ansi")

    assert result.output_lines == 3
    assert (tmp_path / "out.log").read_text(encoding="utf-8") == (
        "FAILED tests/a.py::test_red - boom\nbad � byte\ndone\n"
    )
