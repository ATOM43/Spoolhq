"""Git: local repositories, branches, commits and merges for a project."""

from spoolhq.services.git.repo import GitError, branch_exists, is_work_tree

__all__ = ["GitError", "branch_exists", "is_work_tree"]
