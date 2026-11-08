"""``FakeRunner``: replays a recorded ``stream-json`` transcript instead of a real agent.

Lines go through ``ClaudeStreamParser``, exactly like a real run, and reach the same
callbacks. ``Write`` tool calls inside the worktree write their content, so tests can
check file effects; a ``Write`` outside it ends the run as a policy error. Given several
transcripts, each ``run`` replays the next one, so retries can be tested. No process,
network or model is involved.
"""

import json
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from spoolhq.services.agents.claude_config import ENV_SET, permission_modes, requested_tools
from spoolhq.services.agents.claude_stream import ClaudeStreamParser, PolicyViolation
from spoolhq.services.agents.model import (
    AgentPolicy,
    BackendInfo,
    Budget,
    Outcome,
    RunResult,
)
from spoolhq.services.agents.runner import EventCallback, RawCallback

FAKE_VERSION = "0.0.0-fake"

Render = Callable[[str, str], str]
"""``render(prompt, transcript_text)`` returns the text to replay."""


class FakeRunner:
    """``AgentRunner`` that replays ``transcript`` (one JSON message per line).

    With a sequence, each ``run`` replays the next transcript, and a run past the end
    raises. ``calls`` holds each run's prompt and policy. ``name`` tells fakes registered
    as different backends apart. With ``stall_s``, the run then waits that long like a
    hung agent, so the budget's ``timeout_s`` and ``cancel`` apply as in a real run.
    ``delay_s`` waits between messages, so a run looks live; ``cycle`` starts the
    sequence again instead of raising; ``render`` rewrites a transcript from the prompt.
    """

    def __init__(
        self,
        transcript: Path | Sequence[Path],
        *,
        name: str = "fake",
        stall_s: float = 0,
        delay_s: float = 0,
        cycle: bool = False,
        render: Render | None = None,
    ) -> None:
        self.name = name
        self.stall_s = stall_s
        self.delay_s = delay_s
        self.cycle = cycle
        self.render = render
        # One path is replayed on every run, as before sequences existed.
        self._repeat = isinstance(transcript, Path)
        self.transcripts = (transcript,) if isinstance(transcript, Path) else tuple(transcript)
        self.calls: list[tuple[str, AgentPolicy]] = []

    def detect(self) -> BackendInfo:
        return BackendInfo(
            name=self.name,
            installed=True,
            version=FAKE_VERSION,
            logged_in=True,
            auth_method="claude.ai",
            billing="subscription",
            policy_enforceable=True,
            reason=None,
        )

    def run(
        self,
        prompt: str,
        policy: AgentPolicy,
        budget: Budget,
        *,
        model: str | None = None,
        on_event: EventCallback,
        on_raw: RawCallback | None = None,
        cancel: threading.Event,
    ) -> RunResult:
        index = 0 if self._repeat else len(self.calls)
        if self.cycle:
            index %= len(self.transcripts)
        if index >= len(self.transcripts):
            raise RuntimeError(f"FakeRunner has only {len(self.transcripts)} transcripts")
        transcript = self.transcripts[index]
        self.calls.append((prompt, policy))
        # Checked like the real adapter checks a live run.
        parser = ClaudeStreamParser(
            policy.worktree,
            billing="subscription",
            requested_tools=requested_tools(policy),
            exact_tools=policy.read_only,
            # The environment and flags the real adapter always passes.
            permission_modes=permission_modes(ENV_SET, ("--permission-prompts", "none")),
            backend=self.name,
            backend_version=FAKE_VERSION,
        )
        deadline = time.monotonic() + budget.timeout_s
        text = transcript.read_text(encoding="utf-8")
        if self.render is not None:
            text = self.render(prompt, text)
        for line in text.splitlines():
            if cancel.is_set() or (self.delay_s and line.strip() and cancel.wait(self.delay_s)):
                return parser.finish(Outcome.CANCELLED)
            if time.monotonic() > deadline:
                return parser.finish(Outcome.TIMED_OUT)
            if not line.strip():
                continue
            message = json.loads(line)
            if on_raw is not None:
                on_raw(message)
            try:
                events = parser.feed(message)
            except PolicyViolation as exc:
                return parser.finish(Outcome.ERROR, f"policy not enforced: {exc}")
            outside = self._apply_writes(parser, message)
            for event in events:
                on_event(event)
            if outside is not None:
                return parser.finish(
                    Outcome.ERROR, f"policy not enforced: write outside the worktree: {outside}"
                )
            if budget.max_tokens is not None and parser.weighted_tokens > budget.max_tokens:
                return parser.finish(Outcome.BUDGET_EXHAUSTED)
        if self.stall_s:
            remaining = max(deadline - time.monotonic(), 0)
            if cancel.wait(min(self.stall_s, remaining)):
                return parser.finish(Outcome.CANCELLED)
            if self.stall_s > remaining:
                return parser.finish(Outcome.TIMED_OUT)
        return parser.finish()

    @staticmethod
    def _apply_writes(parser: ClaudeStreamParser, message: Mapping[str, Any]) -> str | None:
        """Performs the message's ``Write`` calls; returns the first path outside the
        worktree, which is not written, or None."""
        if message.get("type") != "assistant":
            return None
        inner = message.get("message")
        content = inner.get("content") if isinstance(inner, Mapping) else None
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, Mapping) or block.get("type") != "tool_use":
                continue
            tool_input = block.get("input")
            if block.get("name") != "Write" or not isinstance(tool_input, Mapping):
                continue
            path, text = tool_input.get("file_path"), tool_input.get("content")
            if not isinstance(path, str) or not isinstance(text, str):
                continue
            relative = parser.relative_path(path)
            if relative is None:
                return path
            target = parser.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8", newline="")
        return None
