"""Writing a merged ticket's notes: PROGRESS.md's managed part, the archive, decisions."""

from datetime import date
from pathlib import Path

import pytest

from spoolhq.services.context import read_repo_docs
from spoolhq.services.notes import (
    END,
    START,
    Decision,
    NotesError,
    RunNote,
    notes_problems,
    write_notes,
)

DAY = date(2026, 11, 20)


def merge(repo: Path, n: int, *decisions: Decision) -> list[str]:
    note = RunNote(f"Added part {n}.\nIt has a second line.", decisions)
    return write_notes(repo, f"T{n:02d}", f"Part {n}", note, DAY)


def entry(n: int) -> str:
    return f"### T{n:02d} · Part {n} (2026-11-20)\n\nAdded part {n}.\nIt has a second line.\n"


def test_a_fresh_repo_gets_progress_markers_and_a_split_index(tmp_path: Path) -> None:
    written = merge(
        tmp_path,
        1,
        Decision("api", "Routes are plural", "Like the rest.\n # not a heading"),
        Decision("data", "SQLite", ""),
    )
    assert written == [
        "PROGRESS.md",
        "DECISIONS.md",
        "docs/decisions/api.md",
        "docs/decisions/data.md",
    ]
    progress = (tmp_path / "PROGRESS.md").read_text(encoding="utf-8")
    assert progress == f"# Progress\n\n{START}\n\n{entry(1)}\n{END}\n"
    assert (tmp_path / "DECISIONS.md").read_text(encoding="utf-8") == (
        "# Decisions\n\n"
        "001 · Routes are plural · docs/decisions/api.md\n"
        "002 · SQLite · docs/decisions/data.md\n"
    )
    assert (tmp_path / "docs/decisions/api.md").read_text(encoding="utf-8") == (
        "# Decisions · api\n\n001. Routes are plural\n    Like the rest.\n     # not a heading\n"
    )
    assert (tmp_path / "docs/decisions/data.md").read_text(encoding="utf-8") == (
        "# Decisions · data\n\n002. SQLite\n"
    )
    assert notes_problems(tmp_path) == []


def test_numbers_continue_after_the_highest_index_line(tmp_path: Path) -> None:
    index = "# Decisions\n\nIntro.\n\n007 · Old · docs/decisions/general.md\n"
    (tmp_path / "DECISIONS.md").write_text(index, encoding="utf-8")
    merge(tmp_path, 1, Decision("general", "New", "Text."))
    assert (tmp_path / "DECISIONS.md").read_text(encoding="utf-8") == (
        index + "008 · New · docs/decisions/general.md\n"
    )
    assert "008. New\n    Text.\n" in (tmp_path / "docs/decisions/general.md").read_text(
        encoding="utf-8"
    )


def test_seven_merges_keep_the_newest_five_and_archive_the_rest(tmp_path: Path) -> None:
    above = "# Our log\r\n\r\nHand-written *summary*  kept as is.\n\xff\n"
    below = "\n## Footer\nAlso kept.\n"
    (tmp_path / "PROGRESS.md").write_bytes(
        above.encode("utf-8", "surrogateescape").replace(b"\xc3\xbf", b"\xff")
        + f"{START}\n{END}\n".encode()
        + below.encode()
    )
    original = (tmp_path / "PROGRESS.md").read_bytes()
    before, after = original.split(START.encode())[0], original.split(END.encode())[1]
    for n in range(1, 8):
        merge(tmp_path, n)
    data = (tmp_path / "PROGRESS.md").read_bytes()
    assert data.startswith(before + START.encode())
    assert data.endswith(END.encode() + after)
    managed = data.decode("utf-8", "surrogateescape").split(START)[1].split(END)[0]
    assert managed == "\n\n" + "\n".join(entry(n) for n in (7, 6, 5, 4, 3)) + "\n"
    archive = (tmp_path / "docs/progress-archive.md").read_text(encoding="utf-8")
    assert archive.endswith(f"\n{entry(1)}\n{entry(2)}")
    assert archive.count("### ") == 2


def test_progress_without_markers_gets_them_at_the_end(tmp_path: Path) -> None:
    old = b"# Progress\n\n## T01 \xc2\xb7 Old entry\n\nNo newline at the end"
    (tmp_path / "PROGRESS.md").write_bytes(old)
    merge(tmp_path, 2)
    data = (tmp_path / "PROGRESS.md").read_bytes()
    assert data.startswith(old)
    assert data[len(old) :] == f"\n\n{START}\n\n{entry(2)}\n{END}\n".encode()


@pytest.mark.parametrize(
    "progress",
    [f"{START}\n", f"{END}\n{START}\n", f"{START}\n{END}\n{START}\n{END}\n"],
)
def test_broken_markers_are_refused(tmp_path: Path, progress: str) -> None:
    (tmp_path / "PROGRESS.md").write_text(progress, encoding="utf-8")
    with pytest.raises(NotesError, match="exactly one spoolhq:recent"):
        merge(tmp_path, 1)


def test_text_inside_the_markers_before_the_entries_is_kept(tmp_path: Path) -> None:
    (tmp_path / "PROGRESS.md").write_text(f"{START}\nSee below.\n{END}\n", encoding="utf-8")
    merge(tmp_path, 1)
    text = (tmp_path / "PROGRESS.md").read_text(encoding="utf-8")
    assert text == f"{START}\n\nSee below.\n\n{entry(1)}\n{END}\n"


def test_a_flat_decisions_file_gets_the_entry_appended(tmp_path: Path) -> None:
    flat = "# Decisions\n\n1. **First.** Because.\n2. **Second.** Also.\n"
    (tmp_path / "DECISIONS.md").write_text(flat, encoding="utf-8")
    written = merge(tmp_path, 3, Decision("api", "Third", "Why.\nMore."))
    assert written == ["PROGRESS.md", "DECISIONS.md"]
    assert (tmp_path / "DECISIONS.md").read_text(encoding="utf-8") == (
        flat + "\n003. Third\n    Why.\n    More.\n"
    )
    assert not (tmp_path / "docs").exists()


def test_without_decisions_an_existing_decisions_file_is_not_touched(tmp_path: Path) -> None:
    (tmp_path / "DECISIONS.md").write_bytes(b"# Why\n\n1. Because.")
    assert merge(tmp_path, 1) == ["PROGRESS.md"]
    assert (tmp_path / "DECISIONS.md").read_bytes() == b"# Why\n\n1. Because."


def test_a_missing_decisions_file_is_created_even_without_decisions(tmp_path: Path) -> None:
    assert merge(tmp_path, 1) == ["PROGRESS.md", "DECISIONS.md"]
    assert (tmp_path / "DECISIONS.md").read_text(encoding="utf-8") == "# Decisions\n"


def test_a_notes_file_linking_outside_the_repo_is_refused(tmp_path: Path) -> None:
    repo, outside = tmp_path / "repo", tmp_path / "outside.md"
    repo.mkdir()
    outside.write_text("secret\n", encoding="utf-8")
    try:
        (repo / "PROGRESS.md").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks need extra rights on this system")
    with pytest.raises(NotesError, match="outside the repository"):
        merge(repo, 1)
    assert outside.read_text(encoding="utf-8") == "secret\n"


def test_the_context_pack_reads_back_what_was_written(tmp_path: Path) -> None:
    merge(tmp_path, 1, Decision("api", "Routes are plural", "Like the rest.\nSecond line."))
    merge(tmp_path, 2, Decision("general", "Dates in UTC", "Always."))
    docs = read_repo_docs(tmp_path, 20)
    assert docs.decisions_selected
    assert docs.decisions_md == (
        "001. Routes are plural\n    Like the rest.\n    Second line.\n"
        "002. Dates in UTC\n    Always.\n"
    )
