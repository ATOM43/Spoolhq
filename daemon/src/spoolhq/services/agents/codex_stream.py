"""Codex CLI's ``codex exec --json`` events turned into SpoolHQ events and a ``RunResult``.

The format is the documented JSON Lines stream: ``thread.started``, ``turn.started``,
``turn.completed`` (with ``usage``), ``turn.failed``, ``item.started|updated|completed``
and ``error``; items are ``agent_message``, ``reasoning``, ``command_execution``,
``file_change``, ``mcp_tool_call``, ``web_search``, ``todo_list`` and ``error``
(https://learn.chatgpt.com/docs/non-interactive-mode, and the TypeScript SDK's
``events.ts`` and ``items.ts``). Like ``ClaudeStreamParser`` it is pure: it only looks at
what it is fed.
"""

import logging
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from spoolhq.core.tokens import weighted_tokens
from spoolhq.services.agents.claude_stream import PolicyViolation, keep_end, summarize
from spoolhq.services.agents.codex_config import BACKEND_NAME
from spoolhq.services.agents.model import (
    AgentEvent,
    FileEdit,
    Message,
    Outcome,
    PermissionDenied,
    RunResult,
    Started,
    ToolCall,
    Usage,
)

logger = logging.getLogger(__name__)

COMMAND = "command_execution"
FILE_CHANGE = "file_change"
KNOWN_TYPES = frozenset(
    {
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "item.started",
        "item.updated",
        "item.completed",
        "error",
    }
)
QUIET_ITEMS = frozenset({"reasoning", "todo_list", "error"})
# Turned off on the command line; one showing up means the configuration didn't hold.
FORBIDDEN_ITEMS = frozenset({"mcp_tool_call", "web_search"})
# Codex reports no denial as such: a failed command whose output says the OS refused it,
# or (network off, as real Codex 0.166.0 shows it) that no host could be reached.
SANDBOX_DENIAL_RE = re.compile(
    r"operation not permitted|permission denied|read-only file system|sandbox"
    r"|could not resolve host|temporary failure in name resolution|network is unreachable",
    re.IGNORECASE,
)
USAGE_LIMIT_RE = re.compile(r"usage limit", re.IGNORECASE)


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


class CodexStreamParser:
    """Feed it each event with ``feed``, then call ``finish`` once.

    ``feed`` raises PolicyViolation when the stream shows something the configuration
    turned off: an MCP tool call, a web search, or a file change by a read-only agent.
    """

    def __init__(
        self,
        worktree: Path,
        *,
        read_only: bool,
        model: str = "",
        backend_version: str = "",
    ) -> None:
        self._root = worktree.resolve()
        self._read_only = read_only
        self.model = model
        self.backend_version = backend_version
        self._started = False
        self._tool_ids: set[str] = set()
        self._usage: list[tuple[int, int, int, int]] = []
        self._files: set[str] = set()
        self._denials: list[PermissionDenied] = []
        self._last_message = ""
        self._items = 0
        self._completed = False
        self._failure: str | None = None
        self._errors: list[str] = []
        self.unknown_events = 0

    # --- totals ---------------------------------------------------------------------

    @property
    def input_tokens(self) -> int:
        return sum(i for i, _, _, _ in self._usage)

    @property
    def output_tokens(self) -> int:
        return sum(o for _, o, _, _ in self._usage)

    @property
    def cache_read_tokens(self) -> int:
        return sum(c for _, _, c, _ in self._usage)

    @property
    def weighted_tokens(self) -> int:
        return weighted_tokens(self.input_tokens, self.output_tokens, self.cache_read_tokens)

    @property
    def has_result(self) -> bool:
        return self._completed or self._failure is not None

    # --- feeding --------------------------------------------------------------------

    def feed(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        kind = message.get("type")
        if kind not in KNOWN_TYPES:
            self.unknown_events += 1
            return []
        if kind == "thread.started":
            if self._started:
                return []
            self._started = True
            return [Started(model=self.model, tools=(), backend_version=self.backend_version)]
        if kind == "turn.started":
            return []
        if kind == "turn.completed":
            return self._turn_completed(message.get("usage"))
        if kind == "turn.failed":
            error = message.get("error")
            text = error.get("message") if isinstance(error, Mapping) else None
            self._failure = str(text or "the turn failed")
            return []
        if kind == "error":
            self._errors.append(str(message.get("message") or "unknown error"))
            return []
        item = message.get("item")
        if not isinstance(item, Mapping):
            self.unknown_events += 1
            return []
        return self._item(kind, item)

    def _turn_completed(self, usage: Any) -> list[AgentEvent]:
        self._completed = True
        usage = usage if isinstance(usage, Mapping) else {}
        # input_tokens already includes the cached part, as SpoolHQ stores it.
        counts = (
            _int(usage.get("input_tokens")),
            _int(usage.get("output_tokens")),
            _int(usage.get("cached_input_tokens")),
            _int(usage.get("cache_write_input_tokens")),
        )
        self._usage.append(counts)
        return [Usage(*counts)] if any(counts) else []

    def _item(self, kind: str, item: Mapping[str, Any]) -> list[AgentEvent]:
        item_type = str(item.get("type", ""))
        if item_type in FORBIDDEN_ITEMS:
            raise PolicyViolation(f"Codex used {item_type}, which SpoolHQ turned off")
        if kind == "item.updated" or item_type in QUIET_ITEMS:
            return []
        item_id = str(item.get("id", ""))
        if item_type == COMMAND:
            return self._command(kind, item_id, item)
        if kind == "item.started":
            return []
        if item_type == "agent_message":
            self._items += 1
            text = item.get("text")
            if isinstance(text, str):
                self._last_message = text
                return [Message(text=text)]
            return []
        if item_type == FILE_CHANGE:
            self._items += 1
            return self._file_change(item_id, item)
        self.unknown_events += 1
        return []

    def _tool_call(self, item_id: str, name: str, value: Any) -> list[AgentEvent]:
        if item_id in self._tool_ids:
            return []
        self._tool_ids.add(item_id)
        return [ToolCall(id=item_id, name=name, input_summary=summarize(value))]

    def _command(self, kind: str, item_id: str, item: Mapping[str, Any]) -> list[AgentEvent]:
        command = item.get("command")
        events = self._tool_call(item_id, COMMAND, command)
        if kind != "item.completed":
            return events
        self._items += 1
        output = item.get("aggregated_output")
        output = output if isinstance(output, str) else ""
        if item.get("status") == "failed" and SANDBOX_DENIAL_RE.search(output):
            reason = output.strip().splitlines()[-1][:500] if output.strip() else "denied"
            events.append(self._deny(COMMAND, summarize(command), f"sandbox: {reason}"))
        return events

    def _file_change(self, item_id: str, item: Mapping[str, Any]) -> list[AgentEvent]:
        raw = item.get("changes")
        changes = [c for c in raw if isinstance(c, Mapping)] if isinstance(raw, list) else []
        events = self._tool_call(item_id, FILE_CHANGE, changes)
        if item.get("status") != "completed":
            return events
        if self._read_only and changes:
            raise PolicyViolation("a read-only Codex run changed files")
        for change in changes:
            path = change.get("path")
            relative = self.relative_path(path) if isinstance(path, str) and path else None
            if relative is None:
                logger.warning(
                    "agent file edit outside the worktree: %s",
                    path,
                    extra={"tool": FILE_CHANGE, "path": path, "worktree": str(self._root)},
                )
            elif relative not in self._files:
                self._files.add(relative)
                events.append(FileEdit(path=relative))
        return events

    def relative_path(self, raw_path: str) -> str | None:
        """``raw_path`` relative to the worktree (``/``-separated), or None if outside."""
        path = Path(raw_path)
        resolved = (path if path.is_absolute() else self._root / path).resolve()
        if resolved == self._root or not resolved.is_relative_to(self._root):
            return None
        return resolved.relative_to(self._root).as_posix()

    def _deny(self, tool: str, input_summary: str, reason: str) -> PermissionDenied:
        denial = PermissionDenied(tool=tool, input_summary=input_summary, reason=reason)
        self._denials.append(denial)
        logger.warning(
            "agent permission denied: %s %s",
            tool,
            input_summary,
            extra={"tool": tool, "input_summary": input_summary, "reason": reason},
        )
        return denial

    # --- the result -----------------------------------------------------------------

    def _outcome(self) -> tuple[Outcome, str | None]:
        if self._failure is None and self._completed:
            return Outcome.COMPLETED, None
        texts = [*filter(None, [self._failure]), *self._errors]
        if any(USAGE_LIMIT_RE.search(text) for text in texts):
            # Codex documents no reset time; the run loop pauses without one.
            return Outcome.USAGE_LIMITED, None
        if texts:
            return Outcome.ERROR, "; ".join(dict.fromkeys(texts))
        return Outcome.ERROR, "Codex ended without completing its turn"

    def finish(self, outcome: Outcome | None = None, error: str | None = None) -> RunResult:
        """The run's result; ``outcome`` (and ``error``) override what the stream says."""
        if outcome is None:
            outcome, error = self._outcome()
        return RunResult(
            outcome=outcome,
            summary=keep_end(self._last_message),
            files_changed=tuple(sorted(self._files)),
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            cost_micro_usd=None,  # Codex reports no cost
            reset_at=None,
            denials=tuple(self._denials),
            num_turns=self._items,
            backend=BACKEND_NAME,
            backend_version=self.backend_version,
            model=self.model,
            error=error,
            debug={"unknown_events": self.unknown_events},
            cache_read_tokens=self.cache_read_tokens,
        )
