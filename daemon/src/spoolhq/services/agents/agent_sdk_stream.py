"""One Agent SDK run: the ``claude`` process behind the SDK and the loop that drives it.

The SDK's own transport starts the CLI with the daemon's whole environment
(``ClaudeAgentOptions.env`` is merged on top of it), so SpoolHQ plugs in its own
``Transport`` (a public SDK interface): the argument list and scrubbed environment the
runner builds, nothing else. The SDK still speaks its control protocol over it
(initialize, the ``PreToolUse`` hook). Every stdout message is tapped before the SDK
parses it, so ``ClaudeStreamParser`` sees exactly what it sees for the Claude Code
adapter. See ``docs/agents.md``.
"""

import json
import re
import signal
import sys
import tempfile
import threading
import time
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import anyio
from anyio.abc import Process
from anyio.streams.text import TextReceiveStream
from claude_agent_sdk import ClaudeAgentOptions, Transport, query

from spoolhq.services.agents.claude_stream import ClaudeStreamParser, PolicyViolation
from spoolhq.services.agents.model import Budget, Outcome, RunResult
from spoolhq.services.agents.process import (
    INTERRUPT_WAIT_S,
    POLL_S,
    STDERR_LINES,
    TERMINATE_WAIT_S,
    _signal_group,
)
from spoolhq.services.agents.runner import EventCallback, RawCallback

Tap = Callable[[dict[str, Any]], None]

# The SDK's control protocol, not the agent's stream: never parsed or transcribed.
CONTROL_TYPES = frozenset({"control_request", "control_response", "control_cancel_request"})
# An API key has no reset time to pause for, so these block the ticket instead.
BILLING_RE = re.compile(r"credit balance|billing|usage limits|quota", re.IGNORECASE)
BILLING_HINT = (
    "the Anthropic API refused the key for billing or quota ({detail}); add credit or "
    "raise the limit at https://platform.claude.com, then retry the ticket"
)


class CliTransport(Transport):
    """The ``claude`` process with SpoolHQ's argv and environment; stderr goes to a temp
    file (no reader to keep up), read once for the error text. ``SdkRun`` sets ``tap``,
    which sees each message before the SDK does; a test double overrides the I/O."""

    def __init__(self, argv: list[str], cwd: Path, env: dict[str, str]) -> None:
        self._argv, self._cwd, self._env = argv, cwd, env
        self.tap: Tap = lambda message: None
        self.invalid_lines = 0
        self._proc: Process | None = None
        self._stderr = tempfile.TemporaryFile()  # read and closed by close()
        self.stderr: list[str] = []
        self._closed = False

    async def connect(self) -> None:
        self._proc = await anyio.open_process(
            self._argv,
            cwd=self._cwd,
            env=self._env,
            stderr=self._stderr,
            # Its own process group, so stopping it reaches the commands it started.
            start_new_session=sys.platform != "win32",
        )

    async def write(self, data: str) -> None:
        if self._proc is not None and self._proc.stdin is not None:
            await self._proc.stdin.send(data.encode("utf-8"))

    async def read_messages(self) -> AsyncIterator[dict[str, Any]]:
        if self._proc is None or self._proc.stdout is None:
            return
        buffer = ""
        async for chunk in TextReceiveStream(self._proc.stdout, errors="replace"):
            *lines, buffer = (buffer + chunk).split("\n")
            for line in lines:
                message = self._parse(line)
                if message is not None:
                    self.tap(message)
                    yield message
        message = self._parse(buffer)
        if message is not None:
            self.tap(message)
            yield message

    def _parse(self, line: str) -> dict[str, Any] | None:
        if not line.strip():
            return None
        try:
            message = json.loads(line)
        except ValueError:
            message = None
        if not isinstance(message, dict):
            self.invalid_lines += 1
            return None
        return message

    async def end_input(self) -> None:
        if self._proc is not None and self._proc.stdin is not None:
            try:
                await self._proc.stdin.aclose()
            except (OSError, anyio.BrokenResourceError, anyio.ClosedResourceError):
                pass

    def is_ready(self) -> bool:
        return self._proc is not None

    async def close(self) -> None:
        """SIGINT, then SIGTERM, then kill, as ``process.Session.stop``; anything left in
        the process group is killed. Safe to call twice."""
        with anyio.CancelScope(shield=True):
            if self._closed:
                return
            self._closed = True
            if self._proc is not None:
                await stop(self._proc)
            self._stderr.seek(0)
            text = self._stderr.read().decode("utf-8", errors="replace")
            self._stderr.close()
            self.stderr = text.splitlines()[-STDERR_LINES:]


async def stop(proc: Process) -> None:
    """SIGINT to the process group, then SIGTERM, then SIGKILL (``terminate`` then ``kill``
    on Windows), as ``process.Session.stop``; then whatever is left in the group."""
    if sys.platform != "win32":
        steps = ((signal.SIGINT, INTERRUPT_WAIT_S), (signal.SIGTERM, TERMINATE_WAIT_S))
        for sig, wait in steps:
            if proc.returncode is not None:
                break
            _signal_group(proc.pid, sig)
            with anyio.move_on_after(wait):
                await proc.wait()
        _signal_group(proc.pid, signal.SIGKILL)  # anything the agent left running
    elif proc.returncode is None:
        proc.terminate()
        with anyio.move_on_after(TERMINATE_WAIT_S):
            await proc.wait()
        if proc.returncode is None:
            proc.kill()
    await proc.aclose()


def billing_error(message: Mapping[str, Any]) -> str | None:
    """The text of a billing or quota failure in ``message``, or None."""
    kind = message.get("type")
    if kind == "assistant" and message.get("error") == "billing_error":
        return "billing_error"
    if kind == "system" and message.get("subtype") == "api_retry":
        return "billing_error" if message.get("error") == "billing_error" else None
    if kind == "result" and message.get("is_error"):
        text = " ".join(str(error) for error in message.get("errors") or ())
        text = text or str(message.get("result") or "")
        return text if BILLING_RE.search(text) else None
    return None


class SdkRun:
    """Drives ``query()`` over a ``Transport`` and turns its stream into a ``RunResult``.

    Callbacks run on the calling thread (``anyio.run``). ``deny`` is for the hook. With
    ``key_source``, an ``init`` naming any other credential (a stored login) stops the run.
    """

    def __init__(
        self,
        transport: CliTransport,
        parser: ClaudeStreamParser,
        budget: Budget,
        on_event: EventCallback,
        on_raw: RawCallback | None,
        cancel: threading.Event,
        key_source: str | None = None,
    ) -> None:
        self._key_source = key_source
        self._transport = transport
        self._parser = parser
        self._budget = budget
        self._on_event = on_event
        self._on_raw = on_raw
        self._cancel = cancel
        self._stopped: tuple[Outcome, str | None] | None = None
        self._sdk_error: str | None = None
        self._billing: str | None = None
        self._scope: anyio.CancelScope | None = None
        transport.tap = self.tap

    def run(self, prompt: str, options: ClaudeAgentOptions) -> RunResult:
        anyio.run(self._main, prompt, options)
        return self._result()

    def deny(self, tool: str, tool_use_id: str, tool_input: Any, reason: str) -> None:
        for event in self._parser.deny(tool, tool_use_id, tool_input, reason):
            self._on_event(event)

    def tap(self, message: dict[str, Any]) -> None:
        """Every message from the CLI, before the SDK sees it."""
        if self._stopped is not None or message.get("type") in CONTROL_TYPES:
            return
        if self._on_raw is not None:
            self._on_raw(message)
        self._billing = self._billing or billing_error(message)
        if message.get("subtype") == "init" and self._key_source:
            source = message.get("apiKeySource")
            if source != self._key_source:
                self._stop(
                    Outcome.ERROR, f"policy not enforced: init reports key source {source!r}"
                )
                return
        try:
            events = self._parser.feed(message)
        except PolicyViolation as exc:
            self._stop(Outcome.ERROR, f"policy not enforced: {exc}")
            return
        for event in events:
            self._on_event(event)
        limit = self._budget.max_tokens
        if limit is not None and self._parser.weighted_tokens > limit:
            self._stop(Outcome.BUDGET_EXHAUSTED)

    def _stop(self, outcome: Outcome, error: str | None = None) -> None:
        if self._stopped is None:
            self._stopped = (outcome, error)
        if self._scope is not None:
            self._scope.cancel()

    async def _watch(self) -> None:
        deadline = time.monotonic() + self._budget.timeout_s
        while True:
            if self._cancel.is_set():
                self._stop(Outcome.CANCELLED)
            elif time.monotonic() >= deadline:
                self._stop(Outcome.TIMED_OUT)
            await anyio.sleep(POLL_S)

    async def _main(self, prompt: str, options: ClaudeAgentOptions) -> None:
        try:
            with anyio.CancelScope() as scope:
                self._scope = scope
                async with anyio.create_task_group() as tasks:
                    tasks.start_soon(self._watch)
                    try:
                        async for _ in query(
                            prompt=prompt, options=options, transport=self._transport
                        ):
                            pass
                    # The SDK raises plain Exception too (a control request timing out).
                    except Exception as exc:  # noqa: BLE001
                        self._sdk_error = str(exc) or type(exc).__name__
                    tasks.cancel_scope.cancel()
        finally:
            await self._transport.close()

    def _result(self) -> RunResult:
        parser = self._parser
        result = parser.finish(*self._stopped) if self._stopped else parser.finish()
        if self._billing is not None and result.outcome in (Outcome.ERROR, Outcome.USAGE_LIMITED):
            result = replace(
                result,
                outcome=Outcome.ERROR,
                reset_at=None,
                error=BILLING_HINT.format(detail=self._billing),
            )
        elif result.outcome is Outcome.ERROR:
            parts = [result.error or "the Agent SDK run failed"]
            if self._sdk_error and not parser.has_result:
                parts.append(self._sdk_error)
            parts += self._transport.stderr
            result = replace(result, error="\n".join(parts))
        if self._transport.invalid_lines:
            debug = {**result.debug, "invalid_lines": self._transport.invalid_lines}
            result = replace(result, debug=debug)
        return result
