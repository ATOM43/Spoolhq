"""``FakeRunner``: replays a recorded ``stream-json`` transcript instead of a real agent.

Lines go through ``ClaudeStreamParser``, exactly like a real run, and reach the same
callbacks. ``Write`` tool calls inside the worktree write their content, so tests can
check file effects. No process, network or model is involved.
"""

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from spoolhq.services.agents.claude_cli import PERMISSION_MODES
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


class FakeRunner:
    """``AgentRunner`` that replays ``transcript`` (one JSON message per line)."""

    name = "fake"

    def __init__(self, transcript: Path) -> None:
        self.transcript = transcript

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
        # Checked like the real adapter checks a live run.
        parser = ClaudeStreamParser(
            policy.worktree,
            billing="subscription",
            permission_modes=PERMISSION_MODES,
            backend=self.name,
            backend_version=FAKE_VERSION,
        )
        for line in self.transcript.read_text(encoding="utf-8").splitlines():
            if cancel.is_set():
                return parser.finish(Outcome.CANCELLED)
            if not line.strip():
                continue
            message = json.loads(line)
            if on_raw is not None:
                on_raw(message)
            try:
                events = parser.feed(message)
            except PolicyViolation as exc:
                return parser.finish(Outcome.ERROR, f"policy not enforced: {exc}")
            self._apply_writes(parser, message)
            for event in events:
                on_event(event)
            if budget.max_tokens is not None and parser.total_tokens > budget.max_tokens:
                return parser.finish(Outcome.BUDGET_EXHAUSTED)
        return parser.finish()

    @staticmethod
    def _apply_writes(parser: ClaudeStreamParser, message: Mapping[str, Any]) -> None:
        if message.get("type") != "assistant":
            return
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
            if relative is not None:
                target = parser.root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8", newline="")
