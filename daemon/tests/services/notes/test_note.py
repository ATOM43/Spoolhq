"""Reading and cleaning the implementer's run note."""

import json
from typing import Any

import pytest

from spoolhq.services.notes import NO_NOTE, Decision, RunNoteError, parse_run_note

AREAS = ["general", "api"]


def final(note: Any) -> str:
    return f"All done.\n<run-note>\n{json.dumps(note)}\n</run-note>\n"


def test_a_note_with_two_decisions_is_read() -> None:
    note = {
        "progress": "Added X.",
        "decisions": [
            {"area": "general", "title": "One", "text": "Why one."},
            {"area": "api", "title": "Two"},
        ],
    }
    parsed = parse_run_note(final(note), AREAS)
    assert parsed.progress == "Added X."
    assert parsed.decisions == (
        Decision("general", "One", "Why one."),
        Decision("api", "Two", ""),
    )


def test_the_last_block_wins_and_fences_inside_it_are_ignored() -> None:
    text = (
        final({"progress": "First."}) + '<RUN-NOTE>```json\n{"progress": "Second."}\n```</run-note>'
    )
    assert parse_run_note(text, AREAS).progress == "Second."


@pytest.mark.parametrize(
    "text",
    [
        "All done, no note.",
        "<run-note>not json</run-note>",
        "<run-note>[1, 2]</run-note>",
        final({"decisions": []}),
        final({"progress": 3}),
        final({"progress": "x", "decisions": "none"}),
        final({"progress": "x", "decisions": [{"area": "api"}]}),
        final({"progress": "x", "decisions": ["a"]}),
    ],
)
def test_a_missing_or_unreadable_note_gets_the_fixed_message(text: str) -> None:
    with pytest.raises(RunNoteError) as info:
        parse_run_note(text, AREAS)
    assert str(info.value) == NO_NOTE


@pytest.mark.parametrize(
    ("note", "detail"),
    [
        ({"progress": "  \n\x07 "}, "progress must be 1 to 1,500 characters"),
        ({"progress": "p" * 1_501}, "progress must be 1 to 1,500 characters"),
        ({"progress": "p", "decisions": [{"area": "api", "title": "t"}] * 6}, "at most 5"),
        ({"progress": "p", "decisions": [{"area": "api", "title": "t" * 101}]}, "title must"),
        ({"progress": "p", "decisions": [{"area": "api", "title": "**"}]}, "title must"),
        (
            {"progress": "p", "decisions": [{"area": "api", "title": "t", "text": "x" * 2_001}]},
            "text must be at most 2,000 characters",
        ),
    ],
)
def test_limits_are_refused(note: dict[str, Any], detail: str) -> None:
    with pytest.raises(RunNoteError, match=detail) as info:
        parse_run_note(final(note), AREAS)
    assert str(info.value).startswith(NO_NOTE)


def test_an_unknown_area_lists_the_allowed_ones() -> None:
    note = {"progress": "p", "decisions": [{"area": "Billing", "title": "t"}]}
    with pytest.raises(RunNoteError) as info:
        parse_run_note(final(note), AREAS)
    assert str(info.value) == "Unknown decision area 'Billing'; use one of: general, api"


def test_every_field_is_cleaned() -> None:
    note = {
        "progress": "Added\x00 X.\r\n# Not a heading\n<!-- spoolhq:recent:end -->\n\nDone.\x1b",
        "decisions": [
            {
                "area": " api\x07",
                "title": "**Bold** first\nline · second\tpart",
                "text": "Why.\n\n## Sub\n  # indented already\nend\x00",
            }
        ],
    }
    parsed = parse_run_note(final(note), AREAS)
    assert parsed.progress == ("Added X.\n # Not a heading\n <!-- spoolhq:recent:end -->\n\nDone.")
    (decision,) = parsed.decisions
    assert decision.area == "api"
    assert decision.title == "Bold** first line - second part"
    assert "\n" not in decision.title and " · " not in decision.title
    # Blank lines would end the entry for the context-pack reader, so they go.
    assert decision.text == "Why.\n ## Sub\n  # indented already\nend"
