from pathlib import Path

import pytest

from spoolhq.services.review import GateLine, ReviewInputs
from spoolhq.services.tickets import read_ticket
from tests.conftest import REVIEW_FIXTURES


@pytest.fixture
def worktree(tmp_path: Path) -> Path:
    path = tmp_path / "worktree"
    path.mkdir()
    return path


@pytest.fixture
def inputs(worktree: Path) -> ReviewInputs:
    """The T07 fixture ticket with the seeded diff; no item checked by the gates."""
    ticket = read_ticket(REVIEW_FIXTURES / "T07-parse-slug.md")
    return ReviewInputs(
        ticket_id=ticket.id,
        title=ticket.meta.title,
        body=ticket.body,
        done_when=tuple(item.text for item in ticket.done_when),
        gate_checked={},
        diff=(REVIEW_FIXTURES / "seeded.diff").read_text(encoding="utf-8"),
        gate_summary=(GateLine("test", "just test", "passed"),),
        worktree=worktree,
    )
