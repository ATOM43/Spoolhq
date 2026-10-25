"""The pull request a run was delivered as (GitHub delivery, T17): stored on the run."""

from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import Run, RunKind, RunStatus
from spoolhq.services.runs.rows import fetch_run


def set_pull_request(run_log: RunLog, run_id: int, number: int, url: str, branch: str) -> Run:
    with run_log.transaction() as tx:
        tx.conn.execute(
            "UPDATE runs SET pr_number = ?, pr_url = ?, pr_branch = ? WHERE id = ?",
            (number, url, branch, run_id),
        )
        return fetch_run(tx.conn, run_id)


def open_pull_requests(run_log: RunLog, limit: int = 500) -> list[Run]:
    """Each ticket's latest run if it waits in ``awaiting_approval`` on a pull request,
    oldest first."""
    latest: dict[str, Run] = {}
    for run in run_log.list_runs(limit=limit):  # newest first
        if run.kind is RunKind.TICKET:
            latest.setdefault(run.ticket_id, run)
    waiting = [
        run
        for run in latest.values()
        if run.pr_number is not None and run.status is RunStatus.AWAITING_APPROVAL
    ]
    return sorted(waiting, key=lambda run: run.id)
