"""Identifier patterns shared by several domains.

The ticket id pattern and its helpers live here, not in ``services/tickets``, because
``services/git`` uses them in branch names and worktree paths and must not import another
service package. ``slugify`` is here for the same reason: branch names (``services/git``)
and the planner's ticket file names (``services/planner``) both use it.
"""

import re
import unicodedata

TICKET_ID_RE = re.compile(r"T\d{2,3}")
TICKET_ID_RULE = "must be T followed by 2 or 3 digits, like T04"

MAX_SLUG_LENGTH = 40
EMPTY_SLUG = "ticket"
_NOT_SLUG_RE = re.compile(r"[^a-z0-9]+")


def check_ticket_id(ticket_id: str) -> str:
    """Return ``ticket_id`` if it is a valid ticket id; raise ValueError otherwise."""
    if not isinstance(ticket_id, str) or not TICKET_ID_RE.fullmatch(ticket_id):
        raise ValueError(f"invalid ticket id {ticket_id!r}: {TICKET_ID_RULE}")
    return ticket_id


def id_key(ticket_id: str) -> tuple[int, str]:
    """Sort key for ticket ids: by number, so ``T99`` comes before ``T100``."""
    return int(ticket_id[1:]), ticket_id


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
