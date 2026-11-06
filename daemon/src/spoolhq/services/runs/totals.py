"""A workspace's totals for Home: usage over every attempt, the latest activity, and the
step a run is on."""

import json
from dataclasses import dataclass

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import EventKind


@dataclass(frozen=True)
class Totals:
    tokens: int
    """Tokens of the attempts that reported no cost (subscription backends)."""
    cost_micro_usd: int | None
    """The summed cost of the attempts that reported one (API-key backends); None if none."""
    last_activity: str | None
    """The latest event's timestamp; None before the first event."""


def project_totals(run_log: RunLog) -> Totals:
    with run_log._reading() as conn:
        tokens, cost = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN cost_micro_usd IS NULL "
            "THEN input_tokens + output_tokens ELSE 0 END), 0), SUM(cost_micro_usd) "
            "FROM attempts"
        ).fetchone()
        last = conn.execute("SELECT ts FROM events ORDER BY id DESC LIMIT 1").fetchone()
    return Totals(int(tokens), cost, last[0] if last else None)


def latest_phase(run_log: RunLog, run_id: int) -> str | None:
    """The ``phase`` of the run's latest ``run.phase`` event (``implement``, ``gates``, …)."""
    with run_log._reading() as conn:
        row = conn.execute(
            "SELECT payload FROM events WHERE run_id = ? AND kind = ? ORDER BY id DESC LIMIT 1",
            (run_id, EventKind.RUN_PHASE.value),
        ).fetchone()
    if row is None:
        return None
    phase = json.loads(row[0]).get("phase")
    return phase if isinstance(phase, str) else None


@dataclass(frozen=True)
class TicketActivity:
    """What the run log holds about one ticket, for its row in the Tickets tab."""

    attempts: int
    tokens: int
    """As in ``Totals``: attempts without a cost."""
    cost_micro_usd: int | None
    run_id: int | None
    """The ticket's latest run."""
    reason: str | None
    """That run's reason (why it is blocked or waits for approval)."""


def ticket_activity(run_log: RunLog) -> dict[str, TicketActivity]:
    """Every ticket with at least one run, by id (plan runs left out)."""
    with run_log._reading() as conn:
        usage = {
            row[0]: row[1:]
            for row in conn.execute(
                "SELECT ticket_id, COUNT(*), COALESCE(SUM(CASE WHEN cost_micro_usd IS NULL "
                "THEN input_tokens + output_tokens ELSE 0 END), 0), SUM(cost_micro_usd) "
                "FROM attempts GROUP BY ticket_id"
            )
        }
        latest = conn.execute(
            "SELECT ticket_id, id, reason FROM runs "
            "WHERE id IN (SELECT MAX(id) FROM runs WHERE kind = 'ticket' GROUP BY ticket_id)"
        ).fetchall()
    found = {}
    for ticket_id, run_id, reason in latest:
        attempts, tokens, cost = usage.get(ticket_id, (0, 0, None))
        found[ticket_id] = TicketActivity(int(attempts), int(tokens), cost, run_id, reason)
    return found
