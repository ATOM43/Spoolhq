"""The notes check: the DECISIONS.md index against the area files."""

from pathlib import Path

import pytest

from spoolhq.services.notes import notes_problems

GOOD_INDEX = (
    "# Decisions\n\n001 · One · docs/decisions/general.md\n002 · Two · docs/decisions/api.md\n"
)


def layout(repo: Path, index: str, general: str, api: str = "002. Two\n    Why.\n") -> None:
    (repo / "docs/decisions").mkdir(parents=True)
    (repo / "DECISIONS.md").write_text(index, encoding="utf-8")
    (repo / "docs/decisions/general.md").write_text(general, encoding="utf-8")
    (repo / "docs/decisions/api.md").write_text(api, encoding="utf-8")


def test_a_matching_index_passes(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "# General\n\n001. One\n    Text.\n    12. not an entry\n")
    assert notes_problems(tmp_path) == []


def test_bold_headings_match_their_index_titles(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "1. **One** and the reason.\n", "2. **Two**\n")
    assert notes_problems(tmp_path) == []


@pytest.mark.parametrize("decisions", [None, "# Decisions\n", "# Decisions\n\n1. Flat entry.\n"])
def test_no_index_has_nothing_to_match(tmp_path: Path, decisions: str | None) -> None:
    if decisions is not None:
        (tmp_path / "DECISIONS.md").write_text(decisions, encoding="utf-8")
    assert notes_problems(tmp_path) == []


def test_a_missing_number_is_caught(tmp_path: Path) -> None:
    index = GOOD_INDEX.replace("002 ·", "003 ·")
    layout(tmp_path, index, "001. One\n", "003. Two\n")
    assert notes_problems(tmp_path) == ["DECISIONS.md: 2 is missing"]


def test_a_duplicate_is_caught(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "001. One\n002. Two\n")
    assert notes_problems(tmp_path) == ["docs/decisions: 2 has 2 entries"]
    (tmp_path / "DECISIONS.md").write_text(GOOD_INDEX + GOOD_INDEX, encoding="utf-8")
    assert notes_problems(tmp_path)[0] == "DECISIONS.md: 1 is listed 2 times"


def test_a_title_mismatch_is_caught(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "001. Uno\n")
    assert notes_problems(tmp_path) == ["DECISIONS.md: 1 title 'One' != heading 'Uno'"]


def test_entries_and_index_lines_without_a_partner_are_caught(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "001. One\n009. Stray\n", "")
    assert notes_problems(tmp_path) == [
        "docs/decisions/general.md: 9 is not in DECISIONS.md",
        "DECISIONS.md: 2 has no entry in docs/decisions/",
    ]


def test_an_entry_in_another_area_file_is_caught(tmp_path: Path) -> None:
    layout(tmp_path, GOOD_INDEX, "001. One\n002. Two\n", "")
    assert notes_problems(tmp_path) == [
        "DECISIONS.md: 2 points to docs/decisions/api.md, but it is in docs/decisions/general.md"
    ]
