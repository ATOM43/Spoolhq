"""Agent events are redacted before they're stored or streamed, and before any cut."""

import json

from spoolhq.services.agents import FileEdit, Message, ToolCall, ToolResult
from spoolhq.services.runloop.transcript import TEXT_LIMIT, event_payload
from spoolhq.services.runs import EventKind

KEY = "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"
HIDDEN = "[redacted: Anthropic key]"


def test_messages_tool_calls_results_and_edits_are_redacted() -> None:
    events = [
        Message(f"I set {KEY}"),
        ToolCall("t1", "Write", json.dumps({"content": f"KEY\n{KEY}"})),
        ToolResult("t1", f"API={KEY}\nok", is_error=False),
        FileEdit(f"keys/{KEY}.txt", 1, 0),
    ]
    payloads = [event_payload(event) for event in events]
    assert KEY not in json.dumps([p[1] for p in payloads if p])
    assert payloads[0] == (EventKind.AGENT_MESSAGE, {"text": f"I set {HIDDEN}"})
    assert payloads[2] is not None and payloads[2][1]["text"] == f"API={HIDDEN}\nok"
    assert payloads[3] is not None and payloads[3][1]["path"] == f"keys/{HIDDEN}.txt"


def test_a_key_across_the_cut_is_redacted_first() -> None:
    text = "x" * (TEXT_LIMIT - 10) + " " + KEY
    found = event_payload(Message(text))
    assert found is not None
    assert "sk-ant-" not in found[1]["text"]
