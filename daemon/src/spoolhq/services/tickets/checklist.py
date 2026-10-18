"""The ``## Done when`` checklist in a ticket's body (read-only)."""

import re

from spoolhq.services.tickets.model import DoneItem

DONE_WHEN = "done when"

_HEADING_RE = re.compile(r" {0,3}(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*")
_ITEM_RE = re.compile(r"[ \t]*[-*+][ \t]+\[([ xX])\](?:[ \t]+(.*?))?[ \t]*")
_FENCE_RE = re.compile(r" {0,3}(`{3,}|~{3,})")

NO_SECTION = "no '## Done when' section"
NO_ITEMS = "the '## Done when' section has no checklist items"


def parse_done_when(body: str) -> tuple[list[DoneItem], list[str]]:
    """The ``- [ ]`` / ``- [x]`` items under the ``## Done when`` heading, and warnings.

    The section runs to the next heading of the same or a higher level. Headings and
    items inside fenced code blocks are ignored. A missing or empty section is a
    warning, not an error.
    """
    items: list[DoneItem] = []
    level: int | None = None  # the Done-when heading's level while inside the section
    found = False
    fence: str | None = None
    for raw in body.split("\n"):
        line = raw.rstrip("\r")
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match[1]
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        heading = _HEADING_RE.fullmatch(line)
        if heading:
            depth = len(heading[1])
            if level is not None and depth <= level:
                level = None
            if level is None and not found and heading[2].casefold() == DONE_WHEN:
                level, found = depth, True
            continue
        if level is not None:
            item = _ITEM_RE.fullmatch(line)
            if item:
                items.append(DoneItem(text=item[2] or "", checked=item[1] != " "))
    if not found:
        return [], [NO_SECTION]
    return items, ([] if items else [NO_ITEMS])
