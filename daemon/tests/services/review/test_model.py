import dataclasses
import threading
from pathlib import Path

from spoolhq.services.agents import FakeRunner
from spoolhq.services.review import ReviewInputs, review
from tests.conftest import REVIEW_FIXTURES


def test_inputs_have_no_field_for_the_implementers_own_account() -> None:
    names = {field.name for field in dataclasses.fields(ReviewInputs)}
    assert names == {
        "ticket_id",
        "title",
        "body",
        "done_when",
        "gate_checked",
        "diff",
        "gate_summary",
        "worktree",
    }
    assert not names & {"transcript", "summary", "progress_note", "implementer_summary"}


def test_each_review_is_its_own_run(inputs: ReviewInputs, home: Path) -> None:
    fake = FakeRunner([REVIEW_FIXTURES / "approve.jsonl", REVIEW_FIXTURES / "approve.jsonl"])
    review(inputs, fake, home=home, cancel=threading.Event())
    review(inputs, fake, home=home, cancel=threading.Event())
    # Two runs (two processes with the real adapter), each given only the prompt.
    first, second = fake.calls
    assert first[0] == second[0]
    assert first[1] == second[1]
