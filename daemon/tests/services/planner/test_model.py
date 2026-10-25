import json
from typing import Any

import pytest
from pydantic import ValidationError

from spoolhq.services.planner import TITLE_MAX, PlannedTicket, clean_title, one_line


def ticket(**changes: Any) -> dict[str, Any]:
    data = {
        "id": "T01",
        "title": "Repository and tooling",
        "phase": 0,
        "purpose": "Set it up.",
        "estimate_h": 2,
        "scope": ["lint and test"],
        "done_when": ["CI passes"],
    }
    return {**data, **changes}


def parse(**changes: Any) -> PlannedTicket:
    return PlannedTicket.model_validate_json(json.dumps(ticket(**changes)))


def test_a_long_title_with_a_newline_becomes_one_clean_line() -> None:
    title = "Build the\nimport " + "x" * 100 + " and more words\t\x07here"
    assert len(title) > 120

    cleaned = parse(title=title).title

    assert "\n" not in cleaned and "\x07" not in cleaned and "\t" not in cleaned
    assert len(cleaned) <= TITLE_MAX
    assert cleaned == clean_title(title)
    assert cleaned.startswith("Build the import xxx")
    assert cleaned == cleaned.strip()


def test_one_line_drops_control_and_format_characters() -> None:
    assert one_line("  a\r\n b​\x1b[31mc  ") == "a b[31mc"


def test_text_fields_are_cleaned_to_one_line() -> None:
    planned = parse(purpose="Two\nlines", scope=["a\nb"], done_when=["x\r\ny"])
    assert (planned.purpose, planned.scope, planned.done_when) == ("Two lines", ("a b",), ("x y",))


@pytest.mark.parametrize(
    ("changes", "location", "message"),
    [
        ({"estimate_h": 6}, "estimate_h", "less than or equal to 4"),
        ({"estimate_h": 1}, "estimate_h", "greater than or equal to 1.5"),
        ({"scope": []}, "scope", "at least 1 item"),
        ({"done_when": []}, "done_when", "at least 1 item"),
        ({"done_when": ["\n"]}, "done_when", "items must not be empty"),
        ({"title": "\x07 \n"}, "title", "must not be empty"),
        ({"id": "T1"}, "id", "must be T followed by 2 or 3 digits"),
        ({"estimate_h": "2"}, "estimate_h", "valid number"),
        ({"extra": 1}, "extra", "Extra inputs are not permitted"),
    ],
)
def test_invalid_tickets_are_refused(changes: dict[str, Any], location: str, message: str) -> None:
    with pytest.raises(ValidationError) as info:
        parse(**changes)
    [error] = info.value.errors()
    assert error["loc"][0] == location
    assert message in error["msg"]
