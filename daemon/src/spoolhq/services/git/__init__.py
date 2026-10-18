"""Git: the project's repository, the worktree each run works in, and its branches.

Every git call goes through ``run_git`` (``runner.py``) as an argument list. A run
works in its own worktree at ``<root>/<project>/<ticket_id>`` on the branch
``feat/<ticket_id>-<slug>`` (``WorktreeManager``); ``recover_worktrees`` cleans up what
a stopped daemon left behind. This package imports no other service. See
``docs/git.md``.
"""

from spoolhq.services.git.naming import branch_name, slugify
from spoolhq.services.git.recovery import (
    RecoveryAction,
    RecoveryEntry,
    RecoveryReport,
    recover_worktrees,
)
from spoolhq.services.git.repo import (
    DirtyRepoError,
    MissingBranchError,
    OperationInProgressError,
    RepoNotReadyError,
    branch_exists,
    default_branch_sha,
    ensure_clean,
    ensure_no_operation_in_progress,
    is_work_tree,
)
from spoolhq.services.git.runner import (
    MIN_GIT_VERSION,
    GitError,
    GitResult,
    check_git_version,
    run_git,
)
from spoolhq.services.git.worktrees import (
    BranchConflictError,
    IdentityError,
    Worktree,
    WorktreeExistsError,
    WorktreeInfo,
    WorktreeManager,
    WorktreeSession,
    WorktreeState,
)

__all__ = [
    "MIN_GIT_VERSION",
    "BranchConflictError",
    "DirtyRepoError",
    "GitError",
    "GitResult",
    "IdentityError",
    "MissingBranchError",
    "OperationInProgressError",
    "RecoveryAction",
    "RecoveryEntry",
    "RecoveryReport",
    "RepoNotReadyError",
    "Worktree",
    "WorktreeExistsError",
    "WorktreeInfo",
    "WorktreeManager",
    "WorktreeSession",
    "WorktreeState",
    "branch_exists",
    "branch_name",
    "check_git_version",
    "default_branch_sha",
    "ensure_clean",
    "ensure_no_operation_in_progress",
    "is_work_tree",
    "recover_worktrees",
    "run_git",
    "slugify",
]
