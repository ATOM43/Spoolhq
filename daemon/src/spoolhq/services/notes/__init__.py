"""Notes: the run note an implementer hands back, and the notes files SpoolHQ writes.

``parse_run_note`` reads and cleans the agent's ``<run-note>`` block; ``write_notes``
puts a merged ticket's progress entry and decisions into ``PROGRESS.md``, the archive,
``DECISIONS.md`` and ``docs/decisions/``; ``notes_problems`` checks that the index and
the area files agree; ``convert_notes`` turns an old flat ``DECISIONS.md`` into that
layout first. Agents never write these files (``is_notes_path``). This package
imports no other service. See ``docs/integration.md``.
"""

from spoolhq.services.notes.check import notes_problems
from spoolhq.services.notes.convert import ConversionError, convert_notes
from spoolhq.services.notes.note import (
    NO_NOTE,
    Decision,
    RunNote,
    RunNoteError,
    clean_text,
    clean_title,
    parse_run_note,
)
from spoolhq.services.notes.write import (
    ARCHIVE,
    DECISIONS,
    DECISIONS_DIR,
    END,
    PROGRESS,
    START,
    NotesError,
    write_notes,
)


def is_notes_path(path: str) -> bool:
    """A file only SpoolHQ writes: an agent's diff must not add or change it."""
    return path in (PROGRESS, DECISIONS, ARCHIVE) or path.startswith(f"{DECISIONS_DIR}/")


__all__ = [
    "ARCHIVE",
    "DECISIONS",
    "DECISIONS_DIR",
    "END",
    "NO_NOTE",
    "PROGRESS",
    "START",
    "ConversionError",
    "Decision",
    "NotesError",
    "RunNote",
    "RunNoteError",
    "clean_text",
    "clean_title",
    "convert_notes",
    "is_notes_path",
    "notes_problems",
    "parse_run_note",
    "write_notes",
]
