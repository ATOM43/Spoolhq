"""``spool tracker push --dry-run``: what a push would send, worked out from the files
and ``state.db`` alone. It writes nothing and calls no tracker, so a task the crash
recovery would adopt shows as a create."""

from pathlib import Path

from spoolhq.services.projects import ProjectError, load_project, project_dir
from spoolhq.services.runs import RunKind, RunLog, RunLogError, outbox
from spoolhq.services.tickets import list_tickets
from spoolhq.services.tracker.base import task_name


def push_plan(project: str, *, projects_dir: Path) -> list[str]:
    """One line per action: create, update (with the status it sets), comment, PR link."""
    tracker = load_project(project, projects_dir=projects_dir).tracker
    if tracker is None:
        raise ProjectError(f"'{project}' has no tracker block in project.yaml")
    statuses = tracker.status_map.model_dump()
    lines = []
    for ticket in list_tickets(project, projects_dir=projects_dir).tickets:
        status = statuses[ticket.meta.status]
        ref = ticket.meta.tracker_ref
        verb = f"update {ref}" if ref else "create"
        lines.append(f"{verb}: {task_name(ticket)} (status: {status})")
    try:
        run_log = RunLog.open_read_only(project_dir(project, projects_dir=projects_dir))
    except (FileNotFoundError, RunLogError):
        return lines  # no run history yet (or not upgraded by the daemon): no comments
    with run_log:
        sent = outbox.queued_keys(run_log)
        baseline = outbox.peek_baseline(run_log)
        for run in reversed(run_log.list_runs(limit=200)):
            if run.kind is not RunKind.TICKET or run.id <= baseline:
                continue
            terminal = run.status.is_terminal and tracker.comment_on_runs
            if terminal and f"comment:{run.id}" not in sent:
                lines.append(f"comment: {run.ticket_id} · run {run.id} {run.status.value}")
            if run.pr_url and f"link_pr:{run.id}" not in sent:
                lines.append(f"comment: {run.ticket_id} · Pull request: {run.pr_url}")
    return lines
