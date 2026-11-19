"""The planner's prompts, rendered with the context service's sandboxed templates.

The spec, the template description, the request and the tickets are untrusted: each is
only ever a variable, escaped for its own tag block, never template source. A project
can override a template with ``<workspace>/prompts/planner.md.j2`` (planning) or
``<workspace>/prompts/ticket-draft.md.j2`` (drafting tickets from a request).
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from spoolhq.services.context import (
    escape_closing_tag,
    keep_connected,
    keep_head,
    render_template,
)
from spoolhq.services.planner.store import Existing
from spoolhq.services.planner.validate import next_id
from spoolhq.services.tickets import Ticket

PLANNER_TEMPLATE = "planner.md.j2"
DRAFT_TEMPLATE = "ticket-draft.md.j2"


def _kept(tickets: Sequence[Ticket]) -> list[dict[str, Any]]:
    def esc(text: str) -> str:
        return escape_closing_tag(text, "kept_tickets")

    return [
        {
            "id": ticket.id,
            "title": esc(ticket.meta.title),
            "status": ticket.meta.status,
            "depends_on": ", ".join(ticket.meta.depends_on),
            "estimate_h": f"{ticket.meta.estimate_h:g}",
            "body": esc(ticket.body),
        }
        for ticket in tickets
    ]


def _code_map(code_map: str | None, chars: int) -> dict[str, Any] | None:
    """``code_map`` (untrusted) cut to ``chars``, least connected parts first."""
    if not code_map or not chars:
        return None
    trimmed = keep_connected(escape_closing_tag(code_map, "code_map"), chars, cap=chars)
    return {"text": trimmed.text, "note": trimmed.note} if trimmed.text.strip() else None


def render_planner_prompt(
    spec: str,
    existing: Existing,
    test_command: str,
    *,
    template_description: str | None = None,
    previous_errors: Sequence[str] | None = None,
    override_dir: Path | None = None,
    code_map: str | None = None,
    code_map_chars: int = 0,
) -> str:
    """The planner's prompt; ``override_dir`` is the workspace's ``prompts/`` folder.
    ``code_map`` (untrusted) is cut to ``code_map_chars``, least connected parts first."""
    variables: dict[str, Any] = {
        "spec": escape_closing_tag(spec, "spec"),
        "template": (
            escape_closing_tag(template_description, "template") if template_description else None
        ),
        "kept": _kept(existing.kept),
        "reusable": [ticket.id for ticket in existing.replaceable],
        "next_id": next_id(existing),
        "test_item": f"`{test_command}` passes",
        "previous_errors": list(previous_errors) if previous_errors else None,
        "code_map": _code_map(code_map, code_map_chars),
    }
    text, _ = render_template(PLANNER_TEMPLATE, variables, override_dir=override_dir)
    return text


def render_draft_prompt(
    request: str,
    spec: str | None,
    tickets: Sequence[Ticket],
    test_command: str,
    *,
    max_chars: int,
    previous_error: str | None = None,
    override_dir: Path | None = None,
    code_map: str | None = None,
    code_map_chars: int = 0,
) -> str:
    """The prompt that drafts tickets from ``request``: the spec (None when there is no
    real one) gets at most half of ``max_chars``, the code map a quarter; the existing
    tickets are listed by id, title, status and phase."""
    trimmed = keep_head(escape_closing_tag(spec, "spec"), max_chars // 2) if spec else None
    variables: dict[str, Any] = {
        "request": escape_closing_tag(request, "request"),
        "spec": (
            {"text": trimmed.text, "note": trimmed.note}
            if trimmed is not None and trimmed.text.strip()
            else None
        ),
        "tickets": [
            {
                "id": ticket.id,
                "title": escape_closing_tag(ticket.meta.title, "tickets"),
                "status": ticket.meta.status,
                "phase": ticket.meta.phase,
            }
            for ticket in tickets
        ],
        "phase": max((ticket.meta.phase for ticket in tickets), default=0),
        "test_item": f"`{test_command}` passes",
        "previous_error": previous_error,
        "code_map": _code_map(code_map, min(code_map_chars, max_chars // 4)),
    }
    text, _ = render_template(DRAFT_TEMPLATE, variables, override_dir=override_dir)
    return text
