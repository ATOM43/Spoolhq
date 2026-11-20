"""Checks on what an attempt may touch: agent settings (blocked, a security issue) and
the notes files only SpoolHQ writes (sent back to the agent), and the ticket's changes
the built-in gates check. All look at the whole branch against a merge base, so main
moving meanwhile never counts.
"""

from spoolhq.services.agents import changed_settings, repo_settings_refusal
from spoolhq.services.gates import FileChange
from spoolhq.services.git import run_git
from spoolhq.services.notes import is_notes_path
from spoolhq.services.runloop.model import Ending, EndKind, RunContext
from spoolhq.services.runs import Attempt, AttemptStatus

# Agent settings at any depth (repo_settings.is_settings_path), so git never lists
# big ignored trees such as node_modules.
SETTINGS_PATHSPECS = (":(glob)**/.claude/**", ":(glob)**/.codex/**", ":(glob)**/.mcp.json")


def _git(ctx: RunContext, *args: str) -> str:
    return run_git(args, ctx.worktree.path).check().stdout


def refused_settings(ctx: RunContext, attempt: Attempt) -> Ending | None:
    """Blocked before any agent starts if a backend of this run would load the repo's
    own agent settings (checked every attempt: an earlier one could have left some)."""
    for runner in (ctx.agents.implementer, ctx.agents.reviewer):
        if refused := repo_settings_refusal(runner, ctx.worktree.path):
            ctx.step("implement", "failed", attempt)
            ctx.run_log.finish_attempt(attempt.id, AttemptStatus.ERROR)
            return Ending(EndKind.BLOCKED, refused)
    return None


def planted_settings(ctx: RunContext, attempt: Attempt) -> Ending | None:
    """Blocked if the branch adds or changes agent settings, committed or git-ignored, so
    they never reach main or the next attempt."""
    committed = _git(ctx, "diff", "--name-only", "-z", f"{ctx.worktree.base_sha}...HEAD")
    ignored = _git(
        ctx,
        "ls-files",
        "-z",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--",
        *SETTINGS_PATHSPECS,
    )
    files = changed_settings([*committed.split("\0"), *ignored.split("\0")])
    if not files:
        return None
    ctx.step("policy", "failed", attempt)
    ctx.run_log.finish_attempt(attempt.id, AttemptStatus.ERROR)
    return Ending(EndKind.BLOCKED, f"The agent changed agent settings: {', '.join(files)}")


def attempt_message(ticket_id: str, number: int) -> str:
    """The subject of an attempt's commit: the agent's work, unlike SpoolHQ's own commits."""
    return f"spool: {ticket_id} attempt {number}"


def _notes_reference(ctx: RunContext) -> str:
    """The newest commit on the branch that no attempt made (the squash pushed to a pull
    request, a merge of main), else the branch's base: the notes files are SpoolHQ's there."""
    prefix = attempt_message(ctx.ticket_id, 0)[:-1]
    log = _git(ctx, "log", "--first-parent", "--format=%H %s", f"{ctx.worktree.base_sha}..HEAD")
    for line in log.splitlines():
        sha, _, subject = line.partition(" ")
        if not subject.startswith(prefix):
            return sha
    return ctx.worktree.base_sha


def edited_notes(ctx: RunContext) -> list[str]:
    """The notes files the attempts add, change or delete (renames count both ways), since
    the merge base with the reference, so main or SpoolHQ changing them never counts."""
    since = f"{_notes_reference(ctx)}...HEAD"
    changed = _git(ctx, "diff", "--name-only", "--no-renames", "-z", since).split("\0")
    return sorted(path for path in changed if is_notes_path(path))


def _merge_base(ctx: RunContext) -> str:
    base = run_git(("merge-base", ctx.project.default_branch, "HEAD"), ctx.worktree.path)
    return base.stdout.strip() if base.returncode == 0 else ctx.worktree.base_sha


def _added_lines(ctx: RunContext, since: str, *paths: str) -> tuple[tuple[int, str], ...]:
    """The lines the ticket adds to one file, numbered in the new file, from ``-U0``.
    Only lines inside hunks count, so an added line starting with ``++`` is still one."""
    diff = _git(
        ctx,
        "diff",
        "-U0",
        "-M",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        since,
        "HEAD",
        "--",
        *paths,
    )
    added: list[tuple[int, str]] = []
    number, in_hunk = 0, False
    for line in diff.split("\n"):
        if line.startswith("@@"):
            in_hunk = True
            number = int(line.split("+", 1)[1].split(",", 1)[0].split(" ", 1)[0])
        elif in_hunk and line.startswith("+"):
            added.append((number, line[1:]))
            number += 1
    return tuple(added)


def ticket_changes(ctx: RunContext, *, with_added: bool = True) -> list[FileChange]:
    """The files the ticket adds, changes, renames or deletes, each with its content
    before the ticket and its added lines, for the built-in gates. "Before" is the merge
    base with the default branch, so main merged into the branch never counts."""
    since = _merge_base(ctx)
    status = _git(ctx, "diff", "--name-status", "-M", "--diff-filter=AMRD", "-z", since, "HEAD")
    fields = iter(status.split("\0"))
    found: list[FileChange] = []
    for kind in fields:
        if not kind:
            continue
        old = new = next(fields)
        renamed = kind.startswith("R")
        if renamed:
            new = next(fields)
        before = None
        if not kind.startswith("A"):
            shown = run_git(("show", f"{since}:{old}"), ctx.worktree.path)
            before = shown.stdout.encode("utf-8") if shown.returncode == 0 else None
        deleted = kind.startswith("D")
        paths = (old, new) if renamed else (new,)
        added = _added_lines(ctx, since, *paths) if with_added and not deleted else ()
        found.append(FileChange(new, before, deleted, old if renamed else None, added))
    return found


def changed_files(ctx: RunContext) -> list[tuple[str, bytes | None]]:
    """The files the ticket adds, changes or renames with their content before it, for
    the file-size gate."""
    return [
        (change.path, change.before)
        for change in ticket_changes(ctx, with_added=False)
        if not change.deleted
    ]
