"""The implementer's prompt for the next attempt: what went wrong last time, the
repository's notes and the code map. The code map is built in the run's worktree before
the first attempt and updated before a retry only if the code changed since; see
``docs/codegraph.md``.
"""

import json
from pathlib import Path
from typing import Any

from spoolhq.services.codegraph import refresh
from spoolhq.services.context import (
    ContextInputs,
    DependencyView,
    GateFailure,
    PreviousAttempt,
    ReviewNote,
    TicketView,
    build_implementer_prompt,
    read_repo_docs,
)
from spoolhq.services.git import conflict_files, run_git
from spoolhq.services.projects import Project, has_spec
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runs import ArtifactName, AttemptKind, AttemptStatus, EventKind, attempt_files
from spoolhq.services.tickets import list_tickets

PROMPTS_DIR = "prompts"
CONTEXT_FILE = "CONTEXT.md"


def code_map(ctx: RunContext) -> str | None:
    """The code map for the next attempt; None when it is off or Graphify can't make it.

    Reused while the worktree's HEAD is the same and nothing is uncommitted; a worktree
    with uncommitted changes (a merge being resolved) is always updated. Once Graphify
    gave no map (missing, failed, timed out), the run doesn't try again: one note, and
    no second timeout.
    """
    if not ctx.project.context.code_map_chars:
        return None
    if ctx.code_map is not None and ctx.code_map[1] is None:
        return None
    path = ctx.worktree.path
    head = run_git(("rev-parse", "HEAD"), path).check().stdout.strip()
    clean = not run_git(("status", "--porcelain"), path).check().stdout.strip()
    key = head if clean else None
    if key is None or ctx.code_map is None or ctx.code_map[0] != key:
        built = refresh(path, ctx.workspace)
        ctx.code_map = (key, built.text if built else None)
    return ctx.code_map[1]


def planner_code_map(project: Project, workspace: Path) -> str | None:
    """The code map of the project's checkout for the planner (read-only, Graphify writes
    only to the cache); None when it is off or unavailable."""
    if not project.context.code_map_chars:
        return None
    built = refresh(project.repo_path, workspace)
    return built.text if built else None


def _read(path: Path) -> str | None:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else None


def previous_attempt(ctx: RunContext, kind: AttemptKind) -> PreviousAttempt | None:
    """What went wrong last time, read from the last finished attempt's files."""
    if kind is AttemptKind.INITIAL:
        return None
    finished = [
        attempt
        for attempt in ctx.run_log.list_attempts(ctx.run.id)
        if attempt.status not in (AttemptStatus.RUNNING, AttemptStatus.INTERRUPTED)
    ]
    if not finished:
        return None
    last = finished[-1]
    files = attempt_files(ctx.workspace, last)
    gates: dict[str, Any] = {}
    reviewed: dict[str, Any] = {}
    if ArtifactName.GATES.value in files:
        gates = json.loads(files[ArtifactName.GATES.value].read_text(encoding="utf-8"))
    if ArtifactName.REVIEW.value in files:
        reviewed = json.loads(files[ArtifactName.REVIEW.value].read_text(encoding="utf-8"))
    note = None
    conflicts: tuple[str, ...] = ()
    if kind is AttemptKind.CONFLICT_RETRY:
        conflicts = conflict_files(ctx.worktree.path)
        note = (
            f"SpoolHQ merged the latest {ctx.project.default_branch} into your branch and these "
            "files conflict. Resolve every conflict marker in them and keep the intent of both "
            "sides; don't run git commands that change anything."
        )
    elif "stopped" in gates:
        note = (
            f"Your last attempt stopped before the checks ran ({gates['stopped']}). "
            "Your changes so far are committed; continue from them."
        )
    elif "stopped" in reviewed:
        note = (
            f"The reviewer stopped before giving a verdict ({reviewed['stopped']}). "
            'Check your work against every "Done when" item.'
        )
    tests = [name for result in gates.get("results", []) for name in result["failing_tests"]]
    feedback: dict[str, Any] = {}
    if kind is AttemptKind.PR_CHANGES:  # stored by polling.py or approval.reject
        events = ctx.run_log.events_since(0, run_id=ctx.run.id, limit=100_000)
        keys = ("pr_review", "user_note")
        logged = [e.payload for e in events if e.kind is EventKind.LOG and e.payload.keys() & keys]
        feedback = logged[-1] if logged else {}
    return PreviousAttempt(
        kind=kind.value,
        number=last.number,
        failing_tests=tuple(dict.fromkeys(tests)),
        gate_failures=tuple(GateFailure(**failure) for failure in gates.get("failures", [])),
        review_notes=tuple(
            ReviewNote(item["item"], item["met"], item["reason"])
            for item in reviewed.get("items", [])
            if not item["met"]
        ),
        conflict_files=conflicts,
        system_note=note,
        pr_review=str(feedback["pr_review"]) if "pr_review" in feedback else None,
        user_note=str(feedback["user_note"]) if "user_note" in feedback else None,
    )


def implementer_prompt(ctx: RunContext, kind: AttemptKind) -> str:
    listing = list_tickets(ctx.project.name, projects_dir=ctx.projects_dir)
    by_id = {ticket.id: ticket for ticket in listing.tickets}
    meta = ctx.ticket.meta
    repo = ctx.project.repo_path
    inputs = ContextInputs(
        ticket=TicketView(
            id=ctx.ticket_id,
            title=meta.title,
            body=ctx.ticket.body,
            depends_on=tuple(
                DependencyView(dep, by_id[dep].meta.title, by_id[dep].meta.status)
                if dep in by_id
                else DependencyView(dep, "(not found)", "missing")
                for dep in meta.depends_on
            ),
            review_required=meta.review_required,
        ),
        # A blank or starter CONTEXT.md is no spec: its section is left out.
        spec=_read(ctx.workspace / CONTEXT_FILE)
        if has_spec(ctx.project.name, projects_dir=ctx.projects_dir)
        else None,
        repo_docs=read_repo_docs(repo, ctx.project.context.decisions_lines),
        commands=ctx.project.commands.for_implementer(),
        previous=previous_attempt(ctx, kind),
        max_chars=ctx.project.context.max_chars,
        progress_entries=ctx.project.context.progress_entries,
        decisions_lines=ctx.project.context.decisions_lines,
        code_map=code_map(ctx),
        code_map_chars=ctx.project.context.code_map_chars,
    )
    return build_implementer_prompt(inputs, override_dir=ctx.workspace / PROMPTS_DIR).text
