"""services/runs/pulls.py: the pull request stored on a run, and the open ones."""

from pathlib import Path

from spoolhq.services.runs import (
    RunLog,
    RunStatus,
    open_pull_requests,
    set_pull_request,
)


def test_open_pull_requests_are_each_tickets_latest_waiting_run(tmp_path: Path) -> None:
    with RunLog(tmp_path, daemon_instance="A") as log:
        old = log.start_run("T01")
        set_pull_request(log, old.id, 1, "u1", "spoolhq/T01-a")
        log.set_run_status(old.id, RunStatus.AWAITING_APPROVAL)
        newer = log.start_run("T01")  # T01's latest run has no PR
        waiting = log.start_run("T02")
        run = set_pull_request(log, waiting.id, 2, "u2", "spoolhq/T02-b")
        assert (run.pr_number, run.pr_url, run.pr_branch) == (2, "u2", "spoolhq/T02-b")
        log.set_run_status(waiting.id, RunStatus.AWAITING_APPROVAL)
        merged = log.start_run("T03")
        set_pull_request(log, merged.id, 3, "u3", "spoolhq/T03-c")
        log.set_run_status(merged.id, RunStatus.DONE)

        assert [r.ticket_id for r in open_pull_requests(log)] == ["T02"]
        assert newer.pr_number is None
