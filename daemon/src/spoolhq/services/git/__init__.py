"""Git: the project's repository, the worktree each run works in, and its branches.

Every git call goes through ``run_git`` (``runner.py``) as an argument list. A run
works in its own worktree at ``<root>/<project>/<ticket_id>`` on the branch
``feat/<ticket_id>-<slug>`` (``WorktreeManager``); ``recover_worktrees`` cleans up what
a stopped daemon left behind; ``integrate.py`` holds the integration mechanics (merge
main into a worktree, squash, fast-forward main, tag). This package imports no other
service. See
``docs/git.md``.
"""

from spoolhq.core.ids import slugify
from spoolhq.services.git.integrate import (
    MergeIn,
    advance,
    commit_message,
    conclude_merge,
    conflict_files,
    create_tag,
    ensure_main_ready,
    is_ancestor,
    is_junk,
    is_secret,
    merge_head,
    merge_in,
    outside_symlinks,
    restore_branch,
    stage,
    start_squash,
    tag_exists,
    too_large,
    unresolved_files,
    unstage,
)
from spoolhq.services.git.integrate import commit as commit_staged
from spoolhq.services.git.naming import branch_name
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
    branch_sha,
    default_branch_sha,
    ensure_clean,
    ensure_no_operation_in_progress,
    has_local_branch,
    is_branch_name,
    is_work_tree,
    operation_in_progress,
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
    remove_path,
)

__all__ = [
    "MergeIn",
    "advance",
    "branch_sha",
    "commit_message",
    "commit_staged",
    "conclude_merge",
    "conflict_files",
    "create_tag",
    "ensure_main_ready",
    "is_ancestor",
    "is_junk",
    "is_secret",
    "merge_head",
    "merge_in",
    "operation_in_progress",
    "outside_symlinks",
    "restore_branch",
    "stage",
    "start_squash",
    "tag_exists",
    "too_large",
    "unresolved_files",
    "unstage",
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
    "branch_name",
    "check_git_version",
    "default_branch_sha",
    "has_local_branch",
    "is_branch_name",
    "ensure_clean",
    "ensure_no_operation_in_progress",
    "is_work_tree",
    "recover_worktrees",
    "remove_path",
    "run_git",
    "slugify",
]
