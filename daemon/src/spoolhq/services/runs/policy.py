"""The merge policy's decision for a run (T18): an event, and the run row's ``policy``."""

from collections.abc import Mapping
from typing import Any

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import EventKind, Run
from spoolhq.services.runs.rows import encode_payload, fetch_run


def record_policy(run_log: RunLog, run_id: int, decision: Mapping[str, Any]) -> Run:
    """Append a ``policy.decision`` event with ``decision`` (``mode`` and ``rules``) and
    store it on the run, in one transaction."""
    with run_log.transaction() as tx:
        tx.append_event(run_id, EventKind.POLICY_DECISION, decision)
        tx.conn.execute(
            "UPDATE runs SET policy = ? WHERE id = ?", (encode_payload(dict(decision)), run_id)
        )
        return fetch_run(tx.conn, run_id)
