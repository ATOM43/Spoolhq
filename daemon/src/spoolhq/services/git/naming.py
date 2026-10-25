"""Branch names for tickets: ``feat/<ticket_id>-<slug>``.

Ticket titles are untrusted text, so the slug keeps only ``a-z``, ``0-9`` and ``-``,
and every name is confirmed with ``git check-ref-format --branch``.
"""

from pathlib import Path

from spoolhq.core.ids import check_ticket_id, slugify
from spoolhq.services.git.runner import GitError, neutral_cwd, run_git

BRANCH_PREFIX = "feat/"


def branch_name(ticket_id: str, title: str, *, cwd: Path | None = None) -> str:
    """The branch for a ticket, checked with ``git check-ref-format --branch``.

    Raises ValueError for an invalid ticket id. A name git refuses would be a bug in
    ``slugify`` and raises GitError.
    """
    name = f"{BRANCH_PREFIX}{check_ticket_id(ticket_id)}-{slugify(title)}"
    result = run_git(["check-ref-format", "--branch", name], cwd or neutral_cwd())
    if result.returncode != 0:
        raise GitError(f"bug: {name!r} is not a valid branch name", command=result.args)
    return name
