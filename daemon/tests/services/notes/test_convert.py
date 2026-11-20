"""Converting an old flat DECISIONS.md to the split layout on the first merge."""

from datetime import date
from pathlib import Path

import pytest

from spoolhq.services.context import read_repo_docs
from spoolhq.services.notes import (
    ConversionError,
    Decision,
    RunNote,
    convert_notes,
    notes_problems,
    write_notes,
)

FLAT = """# Decisions

Notable choices, newest at the bottom.

1. **Generated from a template**: FastAPI and React.
2. **Routes are plural**
   Like the rest of the API.

   A second paragraph, kept.
3. Dates are stored in UTC · always.
- **No ORM events**: they hide writes.
"""


def write(repo: Path, name: str, text: str) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read(repo: Path, name: str) -> str:
    return (repo / name).read_text(encoding="utf-8")


def test_a_flat_file_becomes_an_index_and_general_md_word_for_word(tmp_path: Path) -> None:
    write(tmp_path, "DECISIONS.md", FLAT)
    files, summary = convert_notes(tmp_path)
    assert files == ["DECISIONS.md", "docs/decisions/general.md"]
    assert summary == [
        "DECISIONS.md: moved 4 entries word for word to docs/decisions/general.md; "
        "DECISIONS.md is now the index"
    ]
    assert read(tmp_path, "DECISIONS.md") == (
        "# Decisions\n\nNotable choices, newest at the bottom.\n\n"
        "001 · Generated from a template · docs/decisions/general.md\n"
        "002 · Routes are plural · docs/decisions/general.md\n"
        "003 · Dates are stored in UTC · always. · docs/decisions/general.md\n"
        "004 · No ORM events · docs/decisions/general.md\n"
    )
    assert read(tmp_path, "docs/decisions/general.md") == (
        "# Decisions · general\n\n"
        "001. **Generated from a template**: FastAPI and React.\n\n"
        "002. **Routes are plural**\n   Like the rest of the API.\n\n"
        "   A second paragraph, kept.\n\n"
        "003. Dates are stored in UTC · always.\n\n"
        "004. **No ORM events**: they hide writes.\n"
    )
    assert notes_problems(tmp_path) == []
    # Every word of every entry survives.
    words = read(tmp_path, "docs/decisions/general.md").split()
    for line in FLAT.splitlines()[4:]:
        for word in line.split()[1:]:
            assert word in words


def test_the_next_decision_is_numbered_after_the_converted_ones(tmp_path: Path) -> None:
    write(tmp_path, "DECISIONS.md", FLAT)
    convert_notes(tmp_path)
    note = RunNote("Did it.", (Decision("api", "Paged lists", "Cursor based."),))
    write_notes(tmp_path, "T09", "Lists", note, date(2026, 11, 20))
    assert read(tmp_path, "DECISIONS.md").endswith(
        "004 · No ORM events · docs/decisions/general.md\n"
        "005 · Paged lists · docs/decisions/api.md\n"
    )
    assert notes_problems(tmp_path) == []


def test_the_context_pack_reads_the_converted_decisions(tmp_path: Path) -> None:
    write(tmp_path, "DECISIONS.md", FLAT)
    convert_notes(tmp_path)
    docs = read_repo_docs(tmp_path, 2)
    assert docs.decisions_selected
    assert docs.decisions_md == (
        "003. Dates are stored in UTC · always.\n004. **No ORM events**: they hide writes.\n"
    )


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("# D\n\n1. **A** x\n## Later\n2. **B** y\n", "line 4 isn't part of an entry: ## Later"),
        ("# D\n\n1. **A** x\n1. **B** y\n", "entry 1 appears more than once"),
        ("# D\n\n1. \n", "line 3 is an entry without a title"),
    ],
)
def test_an_unparseable_file_is_refused_and_nothing_written(
    tmp_path: Path, text: str, reason: str
) -> None:
    write(tmp_path, "DECISIONS.md", text)
    with pytest.raises(ConversionError) as caught:
        convert_notes(tmp_path)
    assert str(caught.value) == f"DECISIONS.md couldn't be converted: {reason}"
    assert read(tmp_path, "DECISIONS.md") == text
    assert not (tmp_path / "docs").exists()


@pytest.mark.parametrize(
    "text",
    [
        "# Decisions\n\n001 · A · docs/decisions/general.md\n",
        "# Decisions\n\nIndex below, nothing yet.\n",
    ],
)
def test_a_split_or_empty_layout_is_not_touched(tmp_path: Path, text: str) -> None:
    write(tmp_path, "DECISIONS.md", text)
    write(
        tmp_path,
        "PROGRESS.md",
        "# Progress\n<!-- spoolhq:recent:start -->\n<!-- spoolhq:recent:end -->\n",
    )
    assert convert_notes(tmp_path) == ([], [])
    assert read(tmp_path, "DECISIONS.md") == text


def test_missing_files_need_nothing(tmp_path: Path) -> None:
    assert convert_notes(tmp_path) == ([], [])


def test_progress_without_markers_is_reported_and_left_alone(tmp_path: Path) -> None:
    write(tmp_path, "PROGRESS.md", "# Progress\n\n## T01\n\nOld entry.\n")
    assert convert_notes(tmp_path) == (
        [],
        ["PROGRESS.md: added the spoolhq:recent markers at the end"],
    )
    assert read(tmp_path, "PROGRESS.md") == "# Progress\n\n## T01\n\nOld entry.\n"


def test_a_file_with_only_entries_gets_a_heading(tmp_path: Path) -> None:
    write(tmp_path, "DECISIONS.md", "- First\n- Second\n")
    convert_notes(tmp_path)
    assert read(tmp_path, "DECISIONS.md") == (
        "# Decisions\n\n001 · First · docs/decisions/general.md\n"
        "002 · Second · docs/decisions/general.md\n"
    )
