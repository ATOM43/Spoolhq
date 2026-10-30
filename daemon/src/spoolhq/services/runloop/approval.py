"""The merge policy in a run: the decision on the squash diff, and local approval.

``decide`` runs during integration, after the merge-in of main and the diff guards, on
the staged squash: it gathers the policy's inputs, records the decision (event
``policy.decision`` and the run row) and returns the delivery mode. Without a remote, a
ticket that needs a person waits in ``awaiting_approval`` with its worktree;
``approve`` integrates it and ``reject`` starts a ``pr_changes`` attempt with the
user's note. Like ``polling.py``, the requests use the run loop's own helpers. See
``docs/merge-policy.md``.
"""

import json
from typing import TYPE_CHECKING, Any

from spoolhq.services.git import staged_changes
from spoolhq.services.runloop.model import RunContext, RunLoopError, user_errors
from spoolhq.services.runloop.policy import DeliveryMode, as_record, delivery_mode, evaluate
from spoolhq.services.runs import (
    ArtifactName,
    Attempt,
    AttemptKind,
    AttemptStatus,
    EventKind,
    Run,
    RunLog,
    attempt_files,
    record_policy,
)
from spoolhq.services.tickets import load_ticket

if TYPE_CHECKING:
    from spoolhq.services.runloop.loop import RunLoop

NOTE_REQUIRED = "say what should change with --note"


def read_artifact(ctx: RunContext, attempt: Attempt, name: ArtifactName) -> dict[str, Any]:
    path = attempt_files(ctx.workspace, attempt).get(name.value)
    data = json.loads(path.read_text(encoding="utf-8")) if path is not None else {}
    return data if isinstance(data, dict) else {}


def _user_approved(run_log: RunLog, run: Run, attempt: Attempt) -> bool:
    events = run_log.events_since(0, run_id=run.id, limit=100_000)
    return any(
        e.kind is EventKind.LOG and e.payload.get("approved_attempt") == attempt.id for e in events
    )


def decide(ctx: RunContext, main_sha: str) -> DeliveryMode:
    """Evaluate the policy on the staged squash against ``main_sha`` and record it.

    After ``spool run approve`` of this attempt, hold mode no longer applies and a
    local approval becomes ``direct``: the person has decided."""
    project, attempt = ctx.project, ctx.run_log.list_attempts(ctx.run.id)[-1]
    approved = _user_approved(ctx.run_log, ctx.run, attempt)
    summary = None
    if attempt.status is AttemptStatus.NEEDS_HUMAN:
        summary = str(read_artifact(ctx, attempt, ArtifactName.REVIEW).get("summary") or "")
    decision = evaluate(
        review_required=ctx.ticket.meta.review_required,
        changes=staged_changes(ctx.worktree.path, main_sha),
        max_diff_lines=project.merge_policy.max_diff_lines,
        protected=project.merge_policy.protected(),
        reviewer_summary=summary,
        hold=project.run.integration == "hold" and not approved,
    )
    mode = delivery_mode(decision, project.git.remote is not None)
    extra: dict[str, Any] = {}
    if approved:
        mode = "direct" if mode == "approval" else mode
        extra["approved_by_user"] = True
    ctx.run = record_policy(ctx.run_log, ctx.run.id, as_record(decision, mode, **extra))
    return mode


def approval_message(ctx: RunContext, describe: str) -> str:
    project, tid = ctx.project.name, ctx.ticket_id
    return (
        f"{describe}; approve with `spool run approve {project} {tid}` or reject with "
        f'`spool run reject {project} {tid} --note "..."` — worktree kept at {ctx.worktree.path}'
    )


def _waiting(loop: "RunLoop", run_log: RunLog, project: str, ticket_id: str) -> Run:
    """The ticket's latest run, which must wait in ``awaiting_approval`` without a PR."""
    with user_errors():
        ticket = load_ticket(project, ticket_id, projects_dir=loop.projects_dir)
        runs = run_log.list_runs(ticket_id=ticket_id, limit=1)
    latest, status = runs[0] if runs else None, ticket.meta.status
    if status != "awaiting_approval" or latest is None or latest.status != status:
        raise RunLoopError(f"{ticket_id} is {status}, not awaiting approval")
    if latest.pr_number is not None:
        raise RunLoopError(f"{ticket_id} waits on PR #{latest.pr_number}: {latest.pr_url}")
    return latest


def approve(loop: "RunLoop", project: str, ticket_id: str) -> Run:
    """Integrate a ticket waiting in ``awaiting_approval``: one the policy held for a
    person (that approval is recorded), or one held by a dirty main checkout or an
    interrupted integration (then the policy runs again as usual)."""
    settings, workspace, run_log = loop._project(project)
    with loop._mutex:
        loop._check_free(project)
        latest = _waiting(loop, run_log, project, ticket_id)
        if latest.policy is not None and latest.policy.get("mode") == "approval":
            attempt = run_log.list_attempts(latest.id)[-1]
            payload = {"message": "approved by the user", "approved_attempt": attempt.id}
            run_log.append_event(latest.id, EventKind.LOG, payload)
        return loop._continue(settings, workspace, run_log, latest, None)


def reject(loop: "RunLoop", project: str, ticket_id: str, note: str) -> Run:
    """Send a waiting ticket back to the implementer: a ``pr_changes`` attempt with
    ``note`` as the user's note, then gates, reviewer and policy again."""
    if not note.strip():
        raise RunLoopError(NOTE_REQUIRED)
    settings, workspace, run_log = loop._project(project)
    with loop._mutex:
        loop._check_free(project)
        latest = _waiting(loop, run_log, project, ticket_id)
        payload = {"message": "rejected by the user", "user_note": note.strip()}
        run_log.append_event(latest.id, EventKind.LOG, payload)
        return loop._continue(settings, workspace, run_log, latest, None, AttemptKind.PR_CHANGES)
