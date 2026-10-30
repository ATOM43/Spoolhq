"""One agent CLI process (``claude``, ``codex``): pipes, reader threads, limits, teardown.

``Session`` starts the process with an argument list (never a shell), writes the prompt
to stdin, feeds each stdout line to the backend's stream parser and stops the process
on a timeout, a cancel or the token budget. See ``docs/agents.md``.
"""

import json
import os
import queue
import signal
import subprocess
import sys
import threading
import time
from collections import deque
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import IO, Any, Protocol

from spoolhq.services.agents.claude_stream import PolicyViolation
from spoolhq.services.agents.model import AgentEvent, Budget, Outcome, RunResult
from spoolhq.services.agents.runner import EventCallback, RawCallback

STDERR_LINES = 50
POLL_S = 0.1
EXIT_WAIT_S = 10.0
INTERRUPT_WAIT_S = 10.0
TERMINATE_WAIT_S = 5.0


class StreamParser(Protocol):
    """What ``Session.drive`` needs from a backend's stream parser."""

    @property
    def weighted_tokens(self) -> int: ...

    @property
    def has_result(self) -> bool: ...

    def feed(self, message: Mapping[str, Any]) -> list[AgentEvent]: ...

    def finish(self, outcome: Outcome | None = None, error: str | None = None) -> RunResult: ...


class Session:
    """One agent CLI process (``claude``, ``codex``): its pipes, reader threads and teardown.

    ``label`` names the CLI in an error without a message of its own.
    """

    def __init__(
        self,
        argv: list[str],
        cwd: Path,
        env: dict[str, str],
        prompt: str,
        label: str = "Claude Code",
    ) -> None:
        self.label = label
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr: deque[str] = deque(maxlen=STDERR_LINES)
        options: dict[str, Any] = {}
        if sys.platform != "win32":
            # Its own process group, so stopping it reaches the commands it started.
            options["start_new_session"] = True
        self.proc = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            encoding="utf-8",
            errors="replace",
            **options,
        )
        self.threads = [
            threading.Thread(target=self._write, args=(prompt,), daemon=True),
            threading.Thread(target=self._read_stdout, daemon=True),
            threading.Thread(target=self._read_stderr, daemon=True),
        ]
        for thread in self.threads:
            thread.start()

    def _write(self, prompt: str) -> None:
        stdin = self.proc.stdin
        assert stdin is not None  # noqa: S101 - Popen(stdin=PIPE)
        try:
            stdin.write(prompt)
            stdin.close()
        except (OSError, ValueError):
            pass  # claude exited before reading it all; the run's result says why

    def _read_stdout(self) -> None:
        try:
            for line in _stream(self.proc.stdout):
                self.lines.put(line)
        except (OSError, ValueError):
            pass
        finally:
            self.lines.put(None)

    def _read_stderr(self) -> None:
        try:
            for line in _stream(self.proc.stderr):
                self.stderr.append(line.rstrip("\n"))
        except (OSError, ValueError):
            pass

    def drive(
        self,
        parser: StreamParser,
        budget: Budget,
        on_event: EventCallback,
        on_raw: RawCallback | None,
        cancel: threading.Event,
    ) -> RunResult:
        deadline = time.monotonic() + budget.timeout_s
        stopped: tuple[Outcome, str | None] | None = None
        invalid_lines = 0
        while True:
            if cancel.is_set():
                stopped = (Outcome.CANCELLED, None)
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stopped = (Outcome.TIMED_OUT, None)
                break
            try:
                line = self.lines.get(timeout=min(POLL_S, remaining))
            except queue.Empty:
                continue
            if line is None:
                break
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError:
                message = None
            if not isinstance(message, dict):
                invalid_lines += 1
                continue
            if on_raw is not None:
                on_raw(message)
            try:
                events = parser.feed(message)
            except PolicyViolation as exc:
                stopped = (Outcome.ERROR, f"policy not enforced: {exc}")
                break
            for event in events:
                on_event(event)
            if budget.max_tokens is not None and parser.weighted_tokens > budget.max_tokens:
                stopped = (Outcome.BUDGET_EXHAUSTED, None)
                break

        if stopped is not None:
            self.stop()
            result = parser.finish(*stopped)
        else:
            try:
                self.proc.wait(timeout=max(POLL_S, min(EXIT_WAIT_S, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                self.stop()
            result = parser.finish()
        for thread in self.threads[1:]:
            thread.join(timeout=TERMINATE_WAIT_S)
        if result.outcome is Outcome.ERROR:
            result = replace(result, error=self._error_detail(result.error, parser.has_result))
        if invalid_lines:
            result = replace(result, debug={**result.debug, "invalid_lines": invalid_lines})
        return result

    def _error_detail(self, error: str | None, has_result: bool) -> str:
        parts = [error or f"{self.label} failed"]
        if not has_result and self.proc.returncode is not None:
            parts[0] += f" (exit {self.proc.returncode})"
        if self.stderr:
            parts.append("\n".join(self.stderr))
        return "\n".join(parts)

    def stop(self) -> None:
        """SIGINT, then SIGTERM, then kill (``terminate`` then ``kill`` on Windows)."""
        proc = self.proc
        if proc.poll() is not None:
            return
        if sys.platform != "win32":
            steps = ((signal.SIGINT, INTERRUPT_WAIT_S), (signal.SIGTERM, TERMINATE_WAIT_S))
            for sig, wait in steps:
                _signal_group(proc.pid, sig)
                try:
                    proc.wait(timeout=wait)
                    return
                except subprocess.TimeoutExpired:
                    continue
            _signal_group(proc.pid, signal.SIGKILL)
        else:
            proc.terminate()
            try:
                proc.wait(timeout=TERMINATE_WAIT_S)
                return
            except subprocess.TimeoutExpired:
                proc.kill()
        proc.wait()

    def close(self) -> None:
        """Always run: no process left behind, every pipe closed."""
        try:
            self.stop()
        finally:
            if sys.platform != "win32":
                # Anything the agent left running in claude's process group.
                _signal_group(self.proc.pid, signal.SIGKILL)
            pipes = (self.proc.stdin, self.proc.stdout, self.proc.stderr)
            for thread, pipe in zip(self.threads, pipes, strict=True):
                thread.join(timeout=TERMINATE_WAIT_S)
                # Closing a pipe another thread is still reading or writing would wait
                # on that thread; it only stays open if something outside the process
                # group still holds the other end.
                if pipe is not None and not thread.is_alive():
                    try:
                        pipe.close()
                    except OSError:
                        pass


def _stream(pipe: IO[str] | None) -> Any:
    return iter(pipe.readline, "") if pipe is not None else iter(())


if sys.platform != "win32":

    def _signal_group(pid: int, sig: int) -> None:
        try:
            os.killpg(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass

else:

    def _signal_group(pid: int, sig: int) -> None:
        raise NotImplementedError("process groups are POSIX only")
