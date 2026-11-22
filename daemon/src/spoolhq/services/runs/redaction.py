"""Redacting values the secret scan found from one attempt's stored records.

The named patterns are redacted as text is written (``files.py``, the transcript
recorder). A high-entropy value is only known once the scan flags it, by which time it
may already sit in the attempt's events and files, so ``redact_attempt`` rewrites them.
It is the one exception to append-only events (decision 61): the ``events_no_update``
trigger is dropped and recreated inside the same transaction, so no other writer ever
sees the table without it. ``secure_delete`` and a ``TRUNCATE`` checkpoint keep the old
bytes out of free space and the WAL (best effort: a reader can hold the checkpoint back).
See ``docs/runs.md#redaction``.
"""

import json
from collections.abc import Iterable

from spoolhq.services.gates import HIGH_ENTROPY, marker
from spoolhq.services.runs.files import attempt_dir
from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import Attempt

UPDATE_TRIGGER = "events_no_update"


def _replacer(values: Iterable[str]) -> list[tuple[str, str]]:
    """Each value as written raw and as escaped in JSON, longest first."""
    forms = set()
    for value in values:
        forms |= {value, json.dumps(value)[1:-1], json.dumps(value, ensure_ascii=False)[1:-1]}
    return [(form, marker(HIGH_ENTROPY)) for form in sorted(forms, key=len, reverse=True)]


def _apply(text: str, pairs: list[tuple[str, str]]) -> str:
    for old, new in pairs:
        text = text.replace(old, new)
    return text


def redact_attempt(run_log: RunLog, attempt: Attempt, values: Iterable[str]) -> int:
    """Replace ``values`` in the attempt's files and event rows; the number of rows and
    files changed. The caller holds the project's run lock."""
    pairs = _replacer(values)
    if not pairs:
        return 0
    changed = 0
    for path in attempt_dir(attempt.workspace, attempt).iterdir():
        if path.is_symlink() or not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", errors="surrogateescape")
        if (clean := _apply(text, pairs)) != text:
            path.write_bytes(clean.encode("utf-8", errors="surrogateescape"))
            changed += 1
    with run_log.transaction() as tx:
        tx.conn.execute("PRAGMA secure_delete = ON")
        rows = tx.conn.execute(
            "SELECT id, payload FROM events WHERE attempt_id = ?", (attempt.id,)
        ).fetchall()
        updates = [
            (clean, row_id)
            for row_id, payload in rows
            if (clean := _apply(payload, pairs)) != payload
        ]
        if updates:
            (trigger,) = tx.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
                (UPDATE_TRIGGER,),
            ).fetchone()
            tx.conn.execute("DROP TRIGGER events_no_update")
            tx.conn.executemany("UPDATE events SET payload = ? WHERE id = ?", updates)
            tx.conn.execute(trigger)
    with run_log._lock:  # noqa: SLF001 - same package; a checkpoint can't run in a transaction
        conn = run_log._connection()  # noqa: SLF001
        if updates:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("PRAGMA secure_delete = OFF")
    return changed + len(updates)
