"""The run note the implementer ends its final message with, read and cleaned.

The note is a ``<run-note>`` block holding JSON: ``progress`` (one entry) and up to five
``decisions`` (``area``, ``title``, ``text``). It is agent output that later agents read
from the notes files, so every field is cleaned before it is used: control characters
go, a title is one line without `` · `` (the index separator), and a line starting with
``#`` or ``<!--`` gets a leading space so it can't add a heading or a marker.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

NO_NOTE = "The agent didn't return its run note"
MAX_PROGRESS = 1_500
MAX_DECISIONS = 5
MAX_TITLE = 100
MAX_TEXT = 2_000

_BLOCK = re.compile(r"<run-note>(.*?)</run-note>", re.IGNORECASE | re.DOTALL)
_STRUCTURE = ("#", "<!--")


class RunNoteError(ValueError):
    """The note is missing, unreadable or breaks a rule; the message goes to the agent."""


@dataclass(frozen=True)
class Decision:
    area: str
    title: str
    text: str


@dataclass(frozen=True)
class RunNote:
    progress: str
    decisions: tuple[Decision, ...] = ()


def _no_controls(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    return "".join(c for c in text if c == "\n" or unicodedata.category(c) != "Cc")


def clean_title(text: str) -> str:
    """One line, no `` · ``, no leading ``*`` (so it is never read as a bold heading)."""
    line = " ".join(_no_controls(text).split()).replace(" · ", " - ")
    return line.lstrip("*").strip()


def clean_text(text: str, *, blank_lines: bool = True) -> str:
    """Control characters removed; a line starting with ``#`` or ``<!--`` is indented."""
    lines = [line.rstrip() for line in _no_controls(text).strip().split("\n")]
    if not blank_lines:  # an area entry ends at its first blank line
        lines = [line for line in lines if line.strip()]
    return "\n".join(f" {line}" if line.startswith(_STRUCTURE) else line for line in lines)


def _json(block: str) -> Any:
    start, end = block.find("{"), block.rfind("}")
    if start < 0 or end < start:
        raise RunNoteError(NO_NOTE)
    try:
        return json.loads(block[start : end + 1])
    except ValueError:
        raise RunNoteError(NO_NOTE) from None


def _string(value: Any) -> str:
    if not isinstance(value, str):
        raise RunNoteError(NO_NOTE)
    return value


def parse_run_note(final_text: str, areas: list[str]) -> RunNote:
    """The last ``<run-note>`` block of ``final_text``, cleaned and checked against
    ``areas``; RunNoteError with the message for the agent otherwise."""
    blocks = _BLOCK.findall(final_text)
    data = _json(blocks[-1]) if blocks else None
    if not isinstance(data, dict):
        raise RunNoteError(NO_NOTE)
    progress = clean_text(_string(data.get("progress")))
    raw = data.get("decisions", [])
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise RunNoteError(NO_NOTE)
    if not 1 <= len(progress) <= MAX_PROGRESS:
        raise RunNoteError(f"{NO_NOTE}: progress must be 1 to {MAX_PROGRESS:,} characters")
    if len(raw) > MAX_DECISIONS:
        raise RunNoteError(f"{NO_NOTE}: at most {MAX_DECISIONS} decisions")
    decisions = []
    for item in raw:
        area = _no_controls(_string(item.get("area"))).strip()
        title = clean_title(_string(item.get("title")))
        text = clean_text(_string(item.get("text", "")), blank_lines=False)
        if area not in areas:
            raise RunNoteError(f"Unknown decision area '{area}'; use one of: {', '.join(areas)}")
        if not 1 <= len(title) <= MAX_TITLE:
            raise RunNoteError(f"{NO_NOTE}: a decision title must be 1 to {MAX_TITLE} characters")
        if len(text) > MAX_TEXT:
            raise RunNoteError(
                f"{NO_NOTE}: a decision text must be at most {MAX_TEXT:,} characters"
            )
        decisions.append(Decision(area, title, text))
    return RunNote(progress, tuple(decisions))
