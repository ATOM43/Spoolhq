"""Identifier patterns shared by several domains.

The ticket id pattern lives here, not in ``services/tickets``, because ``services/git``
uses it in branch names and worktree paths and must not import another service package.
"""

import re

TICKET_ID_RE = re.compile(r"T\d{2,3}")
TICKET_ID_RULE = "must be T followed by 2 or 3 digits, like T04"
