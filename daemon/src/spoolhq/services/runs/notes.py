"""The implementer's run note on the run row (T45): its progress entry and decisions."""

import json
from collections.abc import Mapping, Sequence

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import Run
from spoolhq.services.runs.rows import fetch_run


def record_run_note(
    run_log: RunLog, run_id: int, progress: str, decisions: Sequence[Mapping[str, str]]
) -> Run:
    """Store the latest run note on the run; the integration writes it at merge."""
    encoded = json.dumps([dict(item) for item in decisions], ensure_ascii=False)
    with run_log.transaction() as tx:
        fetch_run(tx.conn, run_id)
        tx.conn.execute(
            "UPDATE runs SET progress_note = ?, decisions = ? WHERE id = ?",
            (progress, encoded, run_id),
        )
        return fetch_run(tx.conn, run_id)
