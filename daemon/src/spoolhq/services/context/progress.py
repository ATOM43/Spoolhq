"""The progress note the agent hands back in its final message.

The template asks the agent to end its last message with one ``<progress>…</progress>``
block; T14 appends ``format_progress_entry`` to ``PROGRESS.md`` at merge. The note is
agent output, so it is cleaned before it can reach a file other agents read.
"""

import re
from datetime import date

MAX_NOTE_CHARS = 1_000
NO_NOTE = "No progress note from the agent."

_BLOCK_RE = re.compile(r"<progress>(.*?)</progress>", re.IGNORECASE | re.DOTALL)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _cap(text: str, limit: int = MAX_NOTE_CHARS) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1]
    space = cut.rfind(" ")
    if space > 0:
        cut = cut[:space]
    return cut.rstrip() + "…"


def extract_progress_note(final_text: str) -> str | None:
    """The last ``<progress>`` block's text, one line, at most 1,000 characters.

    ``None`` if there is no block or the last one is empty.
    """
    blocks = _BLOCK_RE.findall(final_text)
    if not blocks:
        return None
    note = _collapse(blocks[-1])
    return _cap(note) if note else None


def _sanitize(note: str) -> str:
    """Drop heading lines and every ``<`` and ``>``, so the note adds no structure."""
    lines = [line for line in note.splitlines() if not line.lstrip().startswith("#")]
    return _collapse(" ".join(lines).replace("<", "").replace(">", ""))


def format_progress_entry(ticket_id: str, title: str, note: str | None, merged_on: date) -> str:
    """The ``PROGRESS.md`` entry for a merged ticket, ending with one newline."""
    text = _cap(_sanitize(note)) if note else ""
    heading = _sanitize(f"{ticket_id} · {title}")
    return f"## {heading} ({merged_on.isoformat()})\n\n{text or NO_NOTE}\n"
