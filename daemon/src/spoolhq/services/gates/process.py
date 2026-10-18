"""Run one gate command: no shell, output streamed to a capped log, process tree stopped
on timeout."""

import codecs
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any

from spoolhq.services.gates.output import clean

OUTPUT_CAP_BYTES = 20_000_000
STOP_WAIT_S = 5.0
READ_CHUNK = 64 * 1024


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int | None
    """``None`` when the command timed out."""
    timed_out: bool
    output_lines: int
    output_truncated: bool


class _Log:
    """Writes cleaned output to the log until the cap, and counts every line."""

    def __init__(self, file: IO[bytes], cap_bytes: int) -> None:
        self.file = file
        self.cap_bytes = cap_bytes
        self.size = 0
        self.lines = 0
        self.truncated = False
        self.ends_with_newline = True
        self.logged_newline = True  # the log so far ends with a newline (or is empty)
        self.closed = False
        self.lock = threading.Lock()

    def drain(self, pipe: IO[bytes]) -> None:
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        for chunk in iter(lambda: pipe.readline(READ_CHUNK), b""):
            self.write(clean(decoder.decode(chunk)))
        self.write(clean(decoder.decode(b"", final=True)))

    def write(self, text: str) -> None:
        if not text:
            return
        with self.lock:
            if self.closed:
                return
            self.lines += text.count("\n")
            self.ends_with_newline = text.endswith("\n")
            if self.truncated:
                return
            data = text.encode("utf-8")
            if self.size + len(data) <= self.cap_bytes:
                self.file.write(data)
                self.size += len(data)
                self.logged_newline = self.ends_with_newline
                return
            self.truncated = True
            ending = b"" if self.logged_newline else b"\n"
            cut = f"[output cut at {self.cap_bytes / 1_000_000:g} MB]\n"
            self.file.write(ending + cut.encode("utf-8"))

    def close(self) -> int:
        """Stop writing; returns the number of lines the command printed."""
        with self.lock:
            self.closed = True
            return self.lines + (0 if self.ends_with_newline else 1)


def run_process(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_s: float,
    log_path: Path,
    cap_bytes: int = OUTPUT_CAP_BYTES,
) -> ProcessResult:
    """Run ``argv`` with stdin closed and stdout and stderr merged into ``log_path``.

    Raises ``OSError`` if the program can't start.
    """
    options: dict[str, Any] = {}
    if sys.platform != "win32":
        options["start_new_session"] = True  # its own process group, stopped as one
    with log_path.open("wb") as file:
        proc = subprocess.Popen(  # noqa: S603 - argument list from shlex, no shell
            list(argv),
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **options,
        )
        assert proc.stdout is not None  # noqa: S101 - stdout=PIPE always sets it
        log = _Log(file, cap_bytes)
        reader = threading.Thread(target=log.drain, args=(proc.stdout,), daemon=True)
        reader.start()
        deadline = time.monotonic() + timeout_s
        timed_out = False
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            _stop_tree(proc)
        if sys.platform != "win32":
            # Anything the command left running in its group, which could hold the pipe.
            _signal_group(proc.pid, signal.SIGKILL)
        reader.join(max(deadline - time.monotonic(), STOP_WAIT_S))
        if reader.is_alive():
            # Something outside the group still holds the pipe (on Windows, a leftover
            # child): the command didn't finish in time.
            timed_out = True
        lines = log.close()
        if not reader.is_alive():
            proc.stdout.close()
    return ProcessResult(
        exit_code=None if timed_out else proc.returncode,
        timed_out=timed_out,
        output_lines=lines,
        output_truncated=log.truncated,
    )


def _stop_tree(proc: "subprocess.Popen[bytes]") -> None:
    """SIGTERM to the process group, SIGKILL after 5 s; ``taskkill /T /F`` on Windows."""
    if sys.platform != "win32":
        _signal_group(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=STOP_WAIT_S)
        except subprocess.TimeoutExpired:
            pass
        _signal_group(proc.pid, signal.SIGKILL)
    else:
        subprocess.run(  # noqa: S603 - fixed argument list, no shell
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],  # noqa: S607 - a Windows system tool
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    proc.wait()


if sys.platform != "win32":

    def _signal_group(pid: int, sig: int) -> None:
        try:
            os.killpg(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass

else:

    def _signal_group(pid: int, sig: int) -> None:
        raise NotImplementedError("process groups are POSIX only")
