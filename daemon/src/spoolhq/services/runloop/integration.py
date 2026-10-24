"""Local integration: an approved run becomes one commit on the local default branch.

``LocalIntegrator`` merges the current main into the run's worktree, reruns the gates
if that brought anything, builds one squash commit (with the ``PROGRESS.md`` entry) on
top of main there, then fast-forwards main to it and tags it. main itself is only ever
fast-forwarded. Every step is written to the integration journal first, so
``recover_integrations`` can finish or undo an integration a crash cut off. The git
mechanics are ``services/git/integrate.py``. See ``docs/integration.md``.
"""

import dataclasses
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from spoolhq.services.context import format_progress_entry
from spoolhq.services.git import (
    DirtyRepoError,
    GitError,
    RepoNotReadyError,
    Worktree,
    WorktreeManager,
    advance,
    branch_sha,
    commit_message,
    commit_staged,
    conclude_merge,
    create_tag,
    default_branch_sha,
    ensure_main_ready,
    is_ancestor,
    is_junk,
    is_secret,
    merge_in,
    operation_in_progress,
    outside_symlinks,
    restore_branch,
    stage,
    start_squash,
    tag_exists,
    too_large,
    unstage,
)
from spoolhq.services.projects import Project
from spoolhq.services.runloop.integrator import IntegrationResult, IntegrationStatus
from spoolhq.services.runloop.machine import run_gates
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runs import (
    EventKind,
    Integration,
    IntegrationState,
    RunLog,
    RunStatus,
    open_integrations,
    set_integration_state,
    start_integration,
    utc_now,
)
from spoolhq.services.scheduler import apply_transition

logger = logging.getLogger(__name__)

MAX_TRIES = 3
PROGRESS_FILE = "PROGRESS.md"
PROGRESS_HEADING = b"# Progress\n"
LISTED_FILES = 100
MOVED = "main kept moving during integration"

Checkpoint = Callable[[str], None]
"""Called with each journal state right after it is committed (tests crash there)."""


def tag_name(ticket_id: str) -> str:
    return f"ticket/{ticket_id}"


def _hint(project: str, ticket_id: str) -> str:
    return f"run spool run integrate {project} {ticket_id}"


def _waiting(project: Project, ticket_id: str, exc: RepoNotReadyError) -> str:
    if isinstance(exc, DirtyRepoError):
        return (
            f"main checkout has uncommitted changes in {project.repo_path}; "
            f"commit or stash them, then {_hint(project.name, ticket_id)}"
        )
    return f"{exc}; then {_hint(project.name, ticket_id)}"


def _result(status: IntegrationStatus, message: str = "") -> IntegrationResult:
    return IntegrationResult(status, message)


def _set_run(run_log: RunLog, run_id: int, status: RunStatus, reason: str | None = None) -> None:
    """Move the run to ``status``, reopening it first if a restart marked it interrupted."""
    run = run_log.get_run(run_id)
    if run.status is status:
        return
    if run.status is RunStatus.INTERRUPTED:
        run_log.reopen_run(run_id)
    elif run.status.is_terminal:
        return
    run_log.set_run_status(run_id, status, reason)


def finish(
    run_log: RunLog,
    manager: WorktreeManager,
    project: str,
    projects_dir: Path,
    journal: Integration,
    branch: str | None,
) -> None:
    """After main advanced: tag, ticket and run ``done``, worktree and branch removed,
    event ``integrate``, journal ``done``. Every step is safe to repeat."""
    sha, tag = journal.commit_sha, tag_name(journal.ticket_id)
    if sha is None:
        raise ValueError(f"integration {journal.id} has no commit")
    create_tag(manager.repo, tag, sha)
    apply_transition(project, journal.ticket_id, "done", projects_dir=projects_dir)
    # Detached during the squash, so git can't name the branch; it is passed in.
    path = manager.path_for(journal.ticket_id)
    if branch is not None:
        manager.teardown(Worktree(journal.ticket_id, branch, path, journal.main_sha, ""))
    else:
        manager.teardown(journal.ticket_id)
    _set_run(run_log, journal.run_id, RunStatus.DONE)
    run_log.append_event(journal.run_id, EventKind.INTEGRATE, {"commit": sha, "tag": tag})
    set_integration_state(run_log, journal.id, IntegrationState.DONE)


class LocalIntegrator:
    """The default integrator: merge, gate, squash, fast-forward, tag (see module doc)."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] = utc_now,
        checkpoint: Checkpoint | None = None,
    ) -> None:
        self.clock = clock
        self.checkpoint = checkpoint

    def integrate(self, ctx: RunContext) -> IntegrationResult:
        for _ in range(MAX_TRIES):
            result = self._once(ctx)
            if result is not None:
                return result
        return _result(IntegrationStatus.FAILED, MOVED)

    def _state(
        self, ctx: RunContext, journal: Integration, state: IntegrationState, sha: str | None = None
    ) -> Integration:
        journal = set_integration_state(ctx.run_log, journal.id, state, commit_sha=sha)
        if self.checkpoint is not None:
            self.checkpoint(state.value)
        return journal

    def _abandon(self, ctx: RunContext, journal: Integration, *, restore: bool) -> None:
        if restore:
            restore_branch(ctx.worktree.path, ctx.worktree.branch)
        set_integration_state(ctx.run_log, journal.id, IntegrationState.ABANDONED)

    def _once(self, ctx: RunContext) -> IntegrationResult | None:
        """One try; None when main moved before it could be advanced."""
        project, tid = ctx.project, ctx.ticket_id
        repo, branch = project.repo_path, project.default_branch
        try:
            ensure_main_ready(repo, branch)
        except RepoNotReadyError as exc:
            return _result(IntegrationStatus.HELD, _waiting(project, tid, exc))
        if tag_exists(repo, tag_name(tid)):
            message = f"tag {tag_name(tid)} already exists; delete it or rename the ticket"
            return _result(IntegrationStatus.FAILED, message)
        main_sha = default_branch_sha(repo, branch)
        journal = start_integration(ctx.run_log, ctx.run.id, tid, branch, main_sha)
        if self.checkpoint is not None:
            self.checkpoint(IntegrationState.MERGING.value)
        try:
            return self._steps(ctx, journal, main_sha)
        except Exception:
            # main not advanced yet: undo the half-built squash so a retry starts clean.
            if branch_sha(repo, branch) == main_sha:
                try:
                    self._abandon(ctx, journal, restore=True)
                except GitError:
                    logger.exception("cannot restore the worktree", extra={"ticket_id": tid})
            raise

    def _steps(
        self, ctx: RunContext, journal: Integration, main_sha: str
    ) -> IntegrationResult | None:
        project, tid = ctx.project, ctx.ticket_id
        repo, branch = project.repo_path, project.default_branch
        path = ctx.worktree.path

        merged = merge_in(path, branch)
        if merged.changed:
            # Diffs for the reviewer are now relative to the main that was merged in.
            ctx.worktree = dataclasses.replace(ctx.worktree, base_sha=main_sha)
        if merged.conflicts:
            self._abandon(ctx, journal, restore=False)  # left mid-merge for the implementer
            return _result(
                IntegrationStatus.CONFLICT,
                f"merge conflict with main in: {', '.join(merged.conflicts)}",
            )
        if merged.changed:
            conclude_merge(path, f"spool: merge {branch} into {ctx.worktree.branch}")
            approved = ctx.run_log.list_attempts(ctx.run.id)[-1]
            gate_run = run_gates(ctx, approved, f"{tid} · integrate")
            if not gate_run.passed:
                self._abandon(ctx, journal, restore=False)
                first = gate_run.first_failure
                return _result(IntegrationStatus.GATES_FAILED, first.command if first else "")

        changed = start_squash(path, main_sha)
        junk = [p for p in changed if is_junk(p)]
        kept = [p for p in changed if not is_junk(p)]
        if junk:
            unstage(path, main_sha, junk)
            ctx.run_log.append_event(
                ctx.run.id,
                EventKind.LOG,
                {
                    "message": "build files left out of the commit",
                    "files": junk[:LISTED_FILES],
                    "count": len(junk),
                },
            )
            listed = ", ".join(junk[:5]) + (f" and {len(junk) - 5} more" if len(junk) > 5 else "")
            ctx.phase("integrate", f"{tid} · integrate · left out build files: {listed}")
        if secrets := [p for p in kept if is_secret(p)]:
            self._abandon(ctx, journal, restore=True)
            message = f"refusing to commit likely secrets: {', '.join(secrets)}"
            return _result(IntegrationStatus.FAILED, message)
        if links := outside_symlinks(path, main_sha):
            self._abandon(ctx, journal, restore=True)
            link, target = links[0]
            message = (
                f"refusing to commit a symlink that points outside the repo: {link} -> {target}"
            )
            return _result(IntegrationStatus.FAILED, message)
        if big := too_large(path, kept):
            self._abandon(ctx, journal, restore=True)
            message = f"file too large to commit: {big[0]} ({big[1] / 2**20:.1f} MB)"
            return _result(IntegrationStatus.FAILED, message)
        self._append_progress(ctx)
        note, title = ctx.run.progress_note, ctx.ticket.meta.title
        sha = commit_staged(path, commit_message(tid, title, note, ctx.run.id))
        journal = self._state(ctx, journal, IntegrationState.COMMITTED, sha)

        try:
            moved = not advance(repo, branch, sha, main_sha)
        except RepoNotReadyError as exc:
            self._abandon(ctx, journal, restore=True)
            return _result(IntegrationStatus.HELD, _waiting(project, tid, exc))
        if moved:
            self._abandon(ctx, journal, restore=True)
            return None
        journal = self._state(ctx, journal, IntegrationState.ADVANCED)
        create_tag(repo, tag_name(tid), sha)
        journal = self._state(ctx, journal, IntegrationState.TAGGED)
        finish(
            ctx.run_log,
            ctx.worktrees,
            project.name,
            ctx.projects_dir,
            journal,
            ctx.worktree.branch,
        )
        ctx.run = ctx.run_log.get_run(ctx.run.id)
        return _result(IntegrationStatus.MERGED, f"{sha[:7]} · {tag_name(tid)}")

    def _append_progress(self, ctx: RunContext) -> None:
        """Append the ticket's entry to ``PROGRESS.md`` in the worktree and stage it."""
        file = ctx.worktree.path / PROGRESS_FILE
        old = file.read_bytes() if file.is_file() else PROGRESS_HEADING
        merged_on = self.clock().astimezone(UTC).date()
        entry = format_progress_entry(
            ctx.ticket_id, ctx.ticket.meta.title, ctx.run.progress_note, merged_on
        )
        file.write_bytes(old.rstrip(b"\r\n") + b"\n\n" + entry.encode("utf-8"))
        stage(ctx.worktree.path, PROGRESS_FILE)


# --- recovery -------------------------------------------------------------------------


def _branch_of(manager: WorktreeManager, journal: Integration) -> str | None:
    """The run's branch, from its SpoolHQ marker (a detached worktree doesn't name it)."""
    for branch, run_id in manager.markers().items():
        if run_id == str(journal.run_id) and branch.startswith(f"feat/{journal.ticket_id}-"):
            return branch
    return None


def recover_integrations(
    run_log: RunLog, project: Project, projects_dir: Path, worktrees_dir: Path
) -> list[str]:
    """Finish or undo the integrations a stopped daemon left open; one line per action.

    main at (or past) the squash commit: the advance happened, so tag, ticket ``done``
    and teardown are finished. main still at ``main_sha``: the worktree is put back on
    its branch and the ticket waits in ``awaiting_approval``. A main checkout with a
    rebase or merge in progress is never touched: it is reported and skipped.
    """
    repo, branch = project.repo_path, project.default_branch
    manager = WorktreeManager(repo, project.name, branch, worktrees_dir)
    actions: list[str] = []
    for journal in open_integrations(run_log):
        tid = journal.ticket_id
        operation = operation_in_progress(repo)
        if operation is not None:
            logger.error(
                "a %s is in progress in the main checkout; integration recovery skipped",
                operation,
                extra={"project": project.name, "ticket_id": tid},
            )
            actions.append(f"{tid}: skipped, a {operation} is in progress in {repo}")
            continue
        run_branch = _branch_of(manager, journal)
        main = branch_sha(repo, branch)
        sha = journal.commit_sha
        if sha is not None and main is not None and is_ancestor(repo, sha, main):
            finish(run_log, manager, project.name, projects_dir, journal, run_branch)
            actions.append(f"{tid}: finished, merged as {sha[:7]}")
            continue
        try:
            ensure_main_ready(repo, branch)
            reason = f"integration interrupted; {_hint(project.name, tid)}"
        except RepoNotReadyError:
            # A fast-forward cut off mid-checkout looks like this: leave it to a person.
            reason = (
                f"integration interrupted while updating {repo}; "
                "check git status there before retrying"
            )
        path = manager.path_for(tid)
        if run_branch is not None and path.is_dir():
            restore_branch(path, run_branch)
        apply_transition(project.name, tid, "awaiting_approval", projects_dir=projects_dir)
        _set_run(run_log, journal.run_id, RunStatus.AWAITING_APPROVAL, reason)
        set_integration_state(run_log, journal.id, IntegrationState.ABANDONED)
        actions.append(f"{tid}: {reason}")
    return actions
