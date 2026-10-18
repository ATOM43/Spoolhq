"""Branch names for tickets: ``feat/<ticket_id>-<slug>``.

Ticket titles are untrusted text, so the slug keeps only ``a-z``, ``0-9`` and ``-``,
and every name is confirmed with ``git check-ref-format --branch``.
"""

import re
import unicodedata
from pathlib import Path

from spoolhq.core.ids import TICKET_ID_RE, TICKET_ID_RULE
from spoolhq.services.git.runner import GitError, neutral_cwd, run_git

BRANCH_PREFIX = "feat/"
MAX_SLUG_LENGTH = 40
EMPTY_SLUG = "ticket"
_NOT_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """``Fix "quoted" thing; rm -rf /`` -> ``fix-quoted-thing-rm-rf``.

    NFKD-normalise and drop non-ASCII characters, lowercase, turn each run of other
    characters into ``-``, strip ``-`` from both ends, cut to 40 characters and strip
    a trailing ``-`` again. An empty result becomes ``ticket``.
    """
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = _NOT_SLUG_RE.sub("-", ascii_title.lower()).strip("-")
    slug = slug[:MAX_SLUG_LENGTH].rstrip("-")
    return slug or EMPTY_SLUG


def check_ticket_id(ticket_id: str) -> str:
    if not isinstance(ticket_id, str) or not TICKET_ID_RE.fullmatch(ticket_id):
        raise ValueError(f"invalid ticket id {ticket_id!r}: {TICKET_ID_RULE}")
    return ticket_id


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
