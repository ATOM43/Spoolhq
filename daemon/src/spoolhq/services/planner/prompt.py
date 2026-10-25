"""The planner's prompt, rendered with the context service's sandboxed templates.

The spec, the template description and the kept tickets are untrusted: each is only
ever a variable, escaped for its own tag block, never template source. A project can
override the template with ``<workspace>/prompts/planner.md.j2``.
"""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from spoolhq.services.context import escape_closing_tag, render_template
from spoolhq.services.planner.store import Existing
from spoolhq.services.planner.validate import next_id
from spoolhq.services.tickets import Ticket

PLANNER_TEMPLATE = "planner.md.j2"


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


def render_planner_prompt(
    spec: str,
    existing: Existing,
    test_command: str,
    *,
    template_description: str | None = None,
    previous_errors: Sequence[str] | None = None,
    override_dir: Path | None = None,
) -> str:
    """The planner's prompt; ``override_dir`` is the workspace's ``prompts/`` folder."""
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
    }
    text, _ = render_template(PLANNER_TEMPLATE, variables, override_dir=override_dir)
    return text
