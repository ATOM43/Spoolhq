"""Crash recovery for worktrees: clean up what a stopped daemon left under the root.

Runs at daemon startup, after run recovery. Only ``<root>/<project>`` is touched, and
branches without the SpoolHQ marker are never deleted. Whether a ticket's worktree
must stay (its run is blocked or awaiting approval) is the caller's call, passed in as
``keep``, so this package needs nothing from the run log.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from spoolhq.services.git.runner import GitError
from spoolhq.services.git.worktrees import WorktreeInfo, WorktreeManager

logger = logging.getLogger(__name__)


class RecoveryAction(StrEnum):
    PRUNED = "pruned"
    REMOVED = "removed"
    REMOVED_ORPHAN = "removed_orphan"
    KEPT = "kept"
    FAILED = "failed"


@dataclass(frozen=True)
class RecoveryEntry:
    ticket_id: str
    path: Path
    action: RecoveryAction
    reason: str


@dataclass(frozen=True)
class RecoveryReport:
    entries: tuple[RecoveryEntry, ...]

    def tickets(self, action: RecoveryAction) -> list[str]:
        """The ticket ids of the entries with ``action``, in report order."""
        return [entry.ticket_id for entry in self.entries if entry.action is action]

    @property
    def pruned(self) -> list[str]:
        return self.tickets(RecoveryAction.PRUNED)

    @property
    def removed(self) -> list[str]:
        return self.tickets(RecoveryAction.REMOVED)

    @property
    def removed_orphan(self) -> list[str]:
        return self.tickets(RecoveryAction.REMOVED_ORPHAN)

    @property
    def kept(self) -> list[str]:
        return self.tickets(RecoveryAction.KEPT)

    @property
    def failed(self) -> list[str]:
        return self.tickets(RecoveryAction.FAILED)


def recover_worktrees(manager: WorktreeManager, keep: Callable[[str], bool]) -> RecoveryReport:
    """Prune, then remove every worktree under the project's root whose ticket isn't kept.

    1. ``git worktree prune`` drops registered worktrees whose folder is gone: ``pruned``.
    2. Registered worktrees whose ticket isn't kept are torn down (branch deleted only
       if it carries the marker): ``removed``.
    3. Folders git doesn't know whose ticket isn't kept are deleted: ``removed_orphan``.
    4. The rest are ``kept``. One that cannot be removed is ``failed`` and logged.

    A second call finds nothing new to do.
    """
    before = manager.list_worktrees()
    manager.prune()
    after = manager.list_worktrees()
    still_registered = {info.ticket_id for info in after if info.registered}

    entries: list[RecoveryEntry] = []
    for info in before:
        if info.registered and not info.folder_exists and info.ticket_id not in still_registered:
            entries.append(
                RecoveryEntry(
                    info.ticket_id, info.path, RecoveryAction.PRUNED, "its folder was missing"
                )
            )
    for info in after:
        entries.append(_recover_one(manager, info, keep))

    for entry in entries:
        level = logging.ERROR if entry.action is RecoveryAction.FAILED else logging.INFO
        logger.log(
            level,
            f"worktree {entry.action.value}",
            extra={
                "project": manager.project,
                "ticket_id": entry.ticket_id,
                "path": str(entry.path),
                "action": entry.action.value,
                "reason": entry.reason,
            },
        )
    return RecoveryReport(tuple(entries))


def _recover_one(
    manager: WorktreeManager, info: WorktreeInfo, keep: Callable[[str], bool]
) -> RecoveryEntry:
    ticket_id, path = info.ticket_id, info.path
    if keep(ticket_id):
        return RecoveryEntry(ticket_id, path, RecoveryAction.KEPT, "its run needs a person")
    try:
        manager.teardown(ticket_id)
    except (GitError, OSError) as exc:
        return RecoveryEntry(ticket_id, path, RecoveryAction.FAILED, str(exc))
    if not info.registered:
        return RecoveryEntry(
            ticket_id, path, RecoveryAction.REMOVED_ORPHAN, "folder not registered with git"
        )
    reason = "left behind by a stopped run"
    if info.branch is not None and not info.has_marker:
        reason += f"; branch {info.branch} has no SpoolHQ marker and was kept"
    return RecoveryEntry(ticket_id, path, RecoveryAction.REMOVED, reason)
