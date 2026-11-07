"""The implementer's live transcript: its normalised ``AgentEvent``s as run-log events.

Each event becomes one ``agent.*`` event of the attempt, so the Run tab can show it live
and load it again later. Text is untrusted and cut to fit the run log's 64 KiB payloads;
the full stream stays in the attempt's ``transcript.jsonl``.
"""

import logging
from typing import Any

from spoolhq.services.agents import (
    AgentEvent,
    FileEdit,
    Message,
    PermissionDenied,
    RateLimit,
    StreamWarning,
    ToolCall,
    ToolResult,
    Usage,
)
from spoolhq.services.runs import Attempt, EventKind, RunLog

logger = logging.getLogger(__name__)

TEXT_LIMIT = 20_000
RESULT_LINES = 200
"""A tool result keeps its first 200 lines (the Run tab shows at most that many)."""


def _result(event: ToolResult) -> dict[str, Any]:
    lines = event.text.splitlines()
    kept = "\n".join(lines[:RESULT_LINES])[:TEXT_LIMIT]
    return {"id": event.id, "text": kept, "lines": len(lines), "is_error": event.is_error}


def event_payload(event: AgentEvent) -> tuple[EventKind, dict[str, Any]] | None:
    """The run-log kind and payload of ``event``; None for those not shown (``Started``)."""
    match event:
        case Message():
            return EventKind.AGENT_MESSAGE, {"text": event.text[:TEXT_LIMIT]}
        case ToolCall():
            call = {"id": event.id, "name": event.name, "input_summary": event.input_summary}
            return EventKind.AGENT_TOOL_CALL, call
        case ToolResult():
            return EventKind.AGENT_TOOL_RESULT, _result(event)
        case FileEdit():
            edit = {"path": event.path, "added": event.added, "removed": event.removed}
            return EventKind.AGENT_FILE_EDIT, edit
        case Usage():
            return EventKind.AGENT_USAGE, {
                "input_tokens": event.input_tokens,
                "output_tokens": event.output_tokens,
                "cache_read_tokens": event.cache_read_tokens,
                "cache_creation_tokens": event.cache_creation_tokens,
            }
        case PermissionDenied():
            return EventKind.AGENT_DENIED, {
                "tool": event.tool,
                "input_summary": event.input_summary,
                "reason": event.reason[:TEXT_LIMIT],
            }
        case RateLimit():
            reset_at = event.reset_at.isoformat() if event.reset_at is not None else None
            return EventKind.AGENT_RATE_LIMIT, {"status": event.status, "reset_at": reset_at}
        case StreamWarning():
            return EventKind.AGENT_WARNING, {"text": event.text[:TEXT_LIMIT], "line": event.line}
    return None


class Recorder:
    """``on_event`` for an agent run: appends each event to the attempt."""

    def __init__(self, run_log: RunLog, attempt: Attempt) -> None:
        self._log = run_log
        self._attempt = attempt

    def __call__(self, event: AgentEvent) -> None:
        found = event_payload(event)
        if found is None:
            return
        kind, payload = found
        try:
            self._log.append_event(self._attempt.run_id, kind, payload, self._attempt.id)
        except ValueError:  # never stop a run over its transcript
            logger.warning("cannot record an agent event", extra={"kind": kind.value})
