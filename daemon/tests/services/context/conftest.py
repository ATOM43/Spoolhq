"""Fixture inputs and golden-file snapshots for the context tests."""

import dataclasses
import os
from pathlib import Path
from typing import Any

from spoolhq.services.context import ContextInputs, DependencyView, RepoDocs, TicketView
from spoolhq.services.tickets import parse_ticket
from tests.conftest import FIXTURES_DIR

CONTEXT_FIXTURES = FIXTURES_DIR / "context"
EXPECTED_DIR = CONTEXT_FIXTURES / "expected"
COMMANDS = {"install": "just install", "lint": "just lint", "test": "just test"}
TICKET_FILE_NAME = "T04-project-workspace-and-settings.md"

# Read at import: the autouse ``home`` fixture clears every SPOOLHQ_* variable.
UPDATE_SNAPSHOTS = os.environ.get("SPOOLHQ_UPDATE_SNAPSHOTS") == "1"


def read_text(path: Path) -> str:
    """The file's text with its line endings untouched."""
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


def fixture_text(name: str) -> str:
    return read_text(CONTEXT_FIXTURES / name)


def fixture_ticket(**changes: Any) -> TicketView:
    ticket = parse_ticket(fixture_text("T04.md"), TICKET_FILE_NAME)
    view = TicketView(
        id=ticket.id,
        title=ticket.meta.title,
        body=ticket.body,
        depends_on=(DependencyView("T02", "Daemon and CLI scaffold", "done"),),
        review_required=ticket.meta.review_required,
    )
    return dataclasses.replace(view, **changes)


def fixture_inputs(**changes: Any) -> ContextInputs:
    inputs = ContextInputs(
        ticket=fixture_ticket(),
        spec=fixture_text("CONTEXT.md"),
        repo_docs=RepoDocs(
            claude_md=fixture_text("CLAUDE.md"),
            progress_md=fixture_text("PROGRESS.md"),
            decisions_md=fixture_text("DECISIONS.md"),
        ),
        commands=dict(COMMANDS),
    )
    return dataclasses.replace(inputs, **changes)


def assert_snapshot(text: str, name: str) -> None:
    """Compare ``text`` with ``expected/<name>`` byte for byte.

    With ``SPOOLHQ_UPDATE_SNAPSHOTS=1`` the file is rewritten instead.
    """
    path = EXPECTED_DIR / name
    if UPDATE_SNAPSHOTS:
        with path.open("w", encoding="utf-8", newline="\n") as file:
            file.write(text)
        return
    assert path.is_file(), f"missing snapshot {name}; run with SPOOLHQ_UPDATE_SNAPSHOTS=1"
    assert text == read_text(path)


def block(text: str, tag: str) -> str:
    """The content between ``<tag>`` and ``</tag>`` (both on their own lines)."""
    start = text.index(f"\n<{tag}>\n") + len(tag) + 4
    end = text.index(f"\n</{tag}>\n", start)
    return text[start:end]
