"""How runs and events are stored in ``state.db``: the columns, rows and payloads."""

import json
import sqlite3
from typing import Any

from spoolhq.services.runs.model import Event, EventKind, Run, RunStatus

MAX_PAYLOAD_BYTES = 64 * 1024

RUN_COLUMNS = "id, ticket_id, status, reason, daemon_instance, started_at, ended_at"
ATTEMPT_COLUMNS = (
    "id, run_id, ticket_id, number, kind, status, dir, backend, model, input_tokens, "
    "output_tokens, cost_micro_usd, started_at, ended_at"
)
EVENT_COLUMNS = "id, run_id, attempt_id, ts, kind, payload"


def encode_payload(payload: Any) -> str:
    """The payload as compact JSON; ValueError if it is not a JSON-serialisable dict
    or is larger than MAX_PAYLOAD_BYTES once encoded."""
    if not isinstance(payload, dict):
        raise ValueError(f"event payload must be a dict, got {type(payload).__name__}")
    try:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"event payload is not JSON-serialisable: {exc}") from exc
    size = len(text.encode("utf-8"))
    if size > MAX_PAYLOAD_BYTES:
        raise ValueError(
            f"event payload is {size} bytes, over the {MAX_PAYLOAD_BYTES}-byte limit; "
            "put large content in the attempt's files"
        )
    return text


def event_kind(kind: EventKind | str) -> EventKind:
    try:
        return EventKind(kind)
    except ValueError:
        known = ", ".join(k.value for k in EventKind)
        raise ValueError(f"unknown event kind {kind!r}; expected one of {known}") from None


def fetch_run(conn: sqlite3.Connection, run_id: int) -> Run:
    """The run with ``run_id``, read on ``conn``; KeyError if there is none."""
    row = conn.execute(f"SELECT {RUN_COLUMNS} FROM runs WHERE id = ?", (run_id,)).fetchone()  # noqa: S608 - constant columns
    if row is None:
        raise KeyError(f"run {run_id} not found")
    return to_run(row)


def to_run(row: tuple[Any, ...]) -> Run:
    return Run(
        id=row[0],
        ticket_id=row[1],
        status=RunStatus(row[2]),
        reason=row[3],
        daemon_instance=row[4],
        started_at=row[5],
        ended_at=row[6],
    )


def to_event(row: tuple[Any, ...]) -> Event:
    return Event(
        id=row[0],
        run_id=row[1],
        attempt_id=row[2],
        ts=row[3],
        kind=EventKind(row[4]),
        payload=json.loads(row[5]),
    )
