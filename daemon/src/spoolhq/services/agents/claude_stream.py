"""Claude Code's ``stream-json`` output turned into events and a ``RunResult``.

``ClaudeStreamParser`` is pure and deterministic: it only looks at the messages it is
fed, in order. The real adapter (``claude_cli.py``) and the fake runner (``fake.py``)
both use it, so recorded transcripts exercise exactly the code real runs go through.
"""

import json
import logging
import re
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from spoolhq.services.agents.model import (
    AgentEvent,
    Billing,
    FileEdit,
    Message,
    Outcome,
    PermissionDenied,
    RateLimit,
    RunResult,
    Started,
    ToolCall,
    Usage,
)

logger = logging.getLogger(__name__)

BACKEND_NAME = "claude-code-cli"
CLAUDE_TOOLS: tuple[str, ...] = ("Read", "Edit", "Write", "Glob", "Grep", "Bash")
"""The built-in tools a Claude Code agent gets (``--tools``)."""
FILE_TOOLS: tuple[str, ...] = ("Read", "Edit", "Write", "Glob", "Grep")
"""The tools approved as a whole (``--allowedTools``); Bash only through command rules."""
EXPECTED_PERMISSION_MODES = frozenset({"dontAsk"})
# Tools that must never show up, even if a future default slipped them in.
FORBIDDEN_TOOLS = frozenset({"WebFetch", "WebSearch"})
EDIT_TOOL_PATH_KEYS = {
    "Edit": "file_path",
    "Write": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}
KNOWN_TYPES = frozenset({"system", "assistant", "user", "result", "rate_limit_event"})
# Partial-message chunks; only sent with --include-partial-messages, and never needed.
IGNORED_TYPES = frozenset({"stream_event"})
SUMMARY_LIMIT = 2000
RESULT_LIMIT = 4000
MICRO = Decimal(1_000_000)
# "Claude AI usage limit reached|1792310400": the epoch is the reset time.
USAGE_LIMIT_RE = re.compile(r"usage limit[^|]*(?:\|\s*(\d+))?", re.IGNORECASE)


class PolicyViolation(Exception):
    """Claude Code did not start with the policy SpoolHQ asked for."""


def summarize(value: Any, limit: int = SUMMARY_LIMIT) -> str:
    """``value`` as compact JSON, cut to ``limit`` characters."""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return text[:limit]


def epoch_to_datetime(value: Any) -> datetime | None:
    """A Unix timestamp (seconds, or milliseconds if it is that large) in UTC."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        seconds = float(value)
        if seconds > 1e11:  # milliseconds
            seconds /= 1000
        return datetime.fromtimestamp(seconds, UTC)
    except (ValueError, OverflowError, OSError):
        return None


def usd_to_micro(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        amount = Decimal(str(value)) * MICRO
        return int(amount.to_integral_value(rounding=ROUND_HALF_UP))
    except (InvalidOperation, ValueError):
        return None


def _int(value: Any) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0


def _usage_counts(usage: Any) -> tuple[int, int, int, int]:
    """(input, output, cache read, cache creation) from a ``usage`` object."""
    if not isinstance(usage, Mapping):
        return (0, 0, 0, 0)
    return (
        _int(usage.get("input_tokens")),
        _int(usage.get("output_tokens")),
        _int(usage.get("cache_read_input_tokens")),
        _int(usage.get("cache_creation_input_tokens")),
    )


def _blocks(message: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    inner = message.get("message")
    content = inner.get("content") if isinstance(inner, Mapping) else None
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, Mapping)]


class ClaudeStreamParser:
    """Feed it each stream message with ``feed``, then call ``finish`` once.

    ``feed`` returns the events for that message and raises PolicyViolation when the
    ``system``/``init`` message shows tools or a permission mode SpoolHQ didn't ask
    for, or when the agent acts before any ``init``.
    """

    def __init__(
        self,
        worktree: Path,
        *,
        billing: Billing,
        requested_tools: Iterable[str] = CLAUDE_TOOLS,
        permission_modes: Iterable[str] = EXPECTED_PERMISSION_MODES,
        backend: str = BACKEND_NAME,
        backend_version: str = "",
    ) -> None:
        self._root = worktree.resolve()
        self._billing = billing
        self._requested = frozenset(requested_tools)
        self._modes = frozenset(permission_modes)
        self._backend = backend
        self.backend_version = backend_version
        self.model = ""
        self._initialised = False
        self._usage: dict[str, tuple[int, int, int, int]] = {}
        self._tool_inputs: dict[str, Any] = {}
        self._pending_edits: dict[str, str] = {}
        self._files: set[str] = set()
        self._denials: list[PermissionDenied] = []
        self._denied_ids: set[str] = set()
        self._limit_rejected = False
        self._assistant_rate_limited = False
        self._reset_at: datetime | None = None
        self._result: Mapping[str, Any] | None = None
        self.unknown_events = 0

    # --- totals ---------------------------------------------------------------------

    @property
    def input_tokens(self) -> int:
        return sum(i + cr + cc for i, _, cr, cc in self._usage.values())

    @property
    def output_tokens(self) -> int:
        return sum(o for _, o, _, _ in self._usage.values())

    @property
    def total_tokens(self) -> int:
        """Tokens so far (input, cached input and output), for the token budget."""
        return self.input_tokens + self.output_tokens

    @property
    def root(self) -> Path:
        """The worktree, resolved."""
        return self._root

    @property
    def has_result(self) -> bool:
        return self._result is not None

    # --- feeding --------------------------------------------------------------------

    def feed(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        kind = message.get("type")
        if kind in IGNORED_TYPES:
            return []
        if kind not in KNOWN_TYPES:
            self.unknown_events += 1
            return []
        if kind == "system":
            return self._system(message)
        if kind == "rate_limit_event":
            return self._rate_limit(message)
        if not self._initialised:
            raise PolicyViolation(f"Claude Code sent {kind!r} before its init message")
        if kind == "assistant":
            return self._assistant(message)
        if kind == "user":
            return self._user(message)
        return self._result_message(message)

    def _system(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        subtype = message.get("subtype")
        if subtype == "init":
            return [self._init(message)]
        if subtype == "permission_denied":
            tool_use_id = str(message.get("tool_use_id", ""))
            reason = message.get("decision_reason") or message.get("message") or "denied"
            return self._deny(str(message.get("tool_name", "")), tool_use_id, None, str(reason))
        if subtype == "api_retry" and message.get("error") == "rate_limit":
            return [RateLimit(status="retrying", reset_at=None)]
        return []

    def _init(self, message: Mapping[str, Any]) -> Started:
        raw_tools = message.get("tools")
        tools = tuple(str(tool) for tool in raw_tools) if isinstance(raw_tools, list) else ()
        unexpected = sorted(
            tool
            for tool in tools
            if tool not in self._requested or tool in FORBIDDEN_TOOLS or tool.startswith("mcp__")
        )
        if unexpected:
            raise PolicyViolation(f"init lists tools that were not requested: {unexpected}")
        mode = message.get("permissionMode")
        if mode not in self._modes:
            expected = " or ".join(sorted(self._modes))
            raise PolicyViolation(f"init reports permission mode {mode!r}, expected {expected}")
        self._initialised = True
        self.model = str(message.get("model", ""))
        version = message.get("claude_code_version")
        if isinstance(version, str) and version:
            self.backend_version = version
        return Started(model=self.model, tools=tools, backend_version=self.backend_version)

    def _rate_limit(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        info = message.get("rate_limit_info")
        info = info if isinstance(info, Mapping) else {}
        status = str(info.get("status", ""))
        reset_at = epoch_to_datetime(info.get("resetsAt"))
        if status == "rejected":
            self._limit_rejected = True
            self._reset_at = reset_at or self._reset_at
        return [RateLimit(status=status, reset_at=reset_at)]

    def _assistant(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        events: list[AgentEvent] = []
        inner = message.get("message")
        inner = inner if isinstance(inner, Mapping) else {}
        if "rate_limit" in (message.get("error"), inner.get("error")):
            self._assistant_rate_limited = True
        message_id = inner.get("id")
        key = str(message_id) if message_id else f"#{len(self._usage)}"
        counts = _usage_counts(inner.get("usage"))
        if key not in self._usage:
            self._usage[key] = counts
            if any(counts):
                events.append(Usage(*counts))
        else:
            # The same message again (one per content block): count it once, keeping
            # the larger figures if it was updated.
            seen = self._usage[key]
            self._usage[key] = (
                max(seen[0], counts[0]),
                max(seen[1], counts[1]),
                max(seen[2], counts[2]),
                max(seen[3], counts[3]),
            )
        for block in _blocks(message):
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                events.append(Message(text=block["text"]))
            elif block.get("type") == "tool_use":
                events.append(self._tool_use(block))
        return events

    def _tool_use(self, block: Mapping[str, Any]) -> ToolCall:
        tool_id = str(block.get("id", ""))
        name = str(block.get("name", ""))
        tool_input = block.get("input")
        self._tool_inputs[tool_id] = tool_input
        path_key = EDIT_TOOL_PATH_KEYS.get(name)
        if path_key is not None and isinstance(tool_input, Mapping):
            raw_path = tool_input.get(path_key)
            if isinstance(raw_path, str) and raw_path:
                relative = self.relative_path(raw_path)
                if relative is None:
                    logger.warning(
                        "agent file edit outside the worktree: %s %s",
                        name,
                        raw_path,
                        extra={"tool": name, "path": raw_path, "worktree": str(self._root)},
                    )
                else:
                    self._pending_edits[tool_id] = relative
        return ToolCall(id=tool_id, name=name, input_summary=summarize(tool_input))

    def relative_path(self, raw_path: str) -> str | None:
        """``raw_path`` relative to the worktree (``/``-separated), or None if outside."""
        path = Path(raw_path)
        if not path.is_absolute():
            path = self._root / path
        resolved = path.resolve()
        if resolved == self._root or not resolved.is_relative_to(self._root):
            return None
        return resolved.relative_to(self._root).as_posix()

    def _user(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        events: list[AgentEvent] = []
        for block in _blocks(message):
            if block.get("type") != "tool_result":
                continue
            relative = self._pending_edits.pop(str(block.get("tool_use_id", "")), None)
            if relative is not None and not block.get("is_error"):
                self._files.add(relative)
                events.append(FileEdit(path=relative))
        return events

    def _deny(self, tool: str, tool_use_id: str, tool_input: Any, reason: str) -> list[AgentEvent]:
        if tool_use_id and tool_use_id in self._denied_ids:
            return []
        self._denied_ids.add(tool_use_id)
        self._pending_edits.pop(tool_use_id, None)
        if tool_input is None:
            tool_input = self._tool_inputs.get(tool_use_id)
        input_summary = summarize(tool_input) if tool_input is not None else ""
        denial = PermissionDenied(tool=tool, input_summary=input_summary, reason=reason)
        self._denials.append(denial)
        logger.warning(
            "agent permission denied: %s %s",
            tool,
            input_summary,
            extra={"tool": tool, "input_summary": input_summary, "reason": reason},
        )
        return [denial]

    def _result_message(self, message: Mapping[str, Any]) -> list[AgentEvent]:
        self._result = message
        events: list[AgentEvent] = []
        denials = message.get("permission_denials")
        for denial in denials if isinstance(denials, list) else []:
            if isinstance(denial, Mapping):
                events += self._deny(
                    str(denial.get("tool_name", "")),
                    str(denial.get("tool_use_id", "")),
                    denial.get("tool_input"),
                    "denied by the permission policy",
                )
        return events

    # --- the result -----------------------------------------------------------------

    def _outcome(self) -> tuple[Outcome, str | None]:
        result = self._result
        if result is None:
            if self._limit_rejected or self._assistant_rate_limited:
                return Outcome.USAGE_LIMITED, None
            return Outcome.ERROR, "Claude Code ended without a result"
        subtype = result.get("subtype")
        if subtype == "success" and not result.get("is_error"):
            return Outcome.COMPLETED, None
        if subtype == "error_max_turns":
            return Outcome.MAX_TURNS, None
        if subtype == "error_max_budget_usd":
            return Outcome.BUDGET_EXHAUSTED, None
        text = self._error_text(result)
        match = USAGE_LIMIT_RE.search(text)
        if match is not None:
            if match.group(1):
                self._reset_at = epoch_to_datetime(match.group(1)) or self._reset_at
            return Outcome.USAGE_LIMITED, None
        if self._limit_rejected or self._assistant_rate_limited:
            return Outcome.USAGE_LIMITED, None
        return Outcome.ERROR, text

    @staticmethod
    def _error_text(result: Mapping[str, Any]) -> str:
        errors = result.get("errors")
        if isinstance(errors, list) and errors:
            return "; ".join(str(error) for error in errors)
        text = result.get("result")
        if isinstance(text, str) and text:
            return text
        return str(result.get("terminal_reason") or result.get("subtype") or "unknown error")

    def finish(self, outcome: Outcome | None = None, error: str | None = None) -> RunResult:
        """The run's result; ``outcome`` (and ``error``) override what the stream says."""
        if outcome is None:
            outcome, error = self._outcome()
        result = self._result or {}
        input_tokens, output_tokens = self.input_tokens, self.output_tokens
        if isinstance(result.get("usage"), Mapping):
            i, o, cr, cc = _usage_counts(result["usage"])
            input_tokens, output_tokens = i + cr + cc, o
        cost = usd_to_micro(result.get("total_cost_usd")) if self._billing == "api" else None
        turns = result.get("num_turns")
        summary = result.get("result")
        return RunResult(
            outcome=outcome,
            summary=summary[:RESULT_LIMIT] if isinstance(summary, str) else "",
            files_changed=tuple(sorted(self._files)),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_micro_usd=cost,
            reset_at=self._reset_at if outcome is Outcome.USAGE_LIMITED else None,
            denials=tuple(self._denials),
            num_turns=_int(turns) if turns is not None else len(self._usage),
            backend=self._backend,
            backend_version=self.backend_version,
            model=self.model,
            error=error,
            debug={"unknown_events": self.unknown_events},
        )
