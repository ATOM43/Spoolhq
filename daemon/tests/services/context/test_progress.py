"""services/context: the agent's progress note."""

from datetime import date

from spoolhq.services.context import extract_progress_note, format_progress_entry


def test_note_is_read_and_collapsed() -> None:
    text = "done\n<progress>Added the workspace\nfolder.</progress>"
    assert extract_progress_note(text) == "Added the workspace folder."


def test_last_block_wins_and_tags_are_case_insensitive() -> None:
    text = "<progress>First.</progress> later <PROGRESS>  Second   note. </Progress>"
    assert extract_progress_note(text) == "Second note."


def test_missing_or_empty_block_is_none() -> None:
    assert extract_progress_note("All done, no note.") is None
    assert extract_progress_note("<progress>  \n </progress>") is None


def test_long_note_is_cut_at_a_word() -> None:
    note = extract_progress_note("<progress>" + "word " * 600 + "</progress>")
    assert note is not None
    assert len(note) <= 1_000
    assert note.endswith("word…")


def test_note_cannot_add_headings_or_tags() -> None:
    entry = format_progress_entry(
        "T04", "Project workspace and settings", "# Hacked\n<script>ok</script>", date(2026, 10, 18)
    )
    assert "<" not in entry and ">" not in entry
    assert [line for line in entry.splitlines() if line.startswith("#")] == [
        "## T04 · Project workspace and settings (2026-10-18)"
    ]
    assert entry.endswith("scriptok/script\n")


def test_entry_without_a_note() -> None:
    assert format_progress_entry(
        "T04", "Project workspace and settings", None, date(2026, 10, 18)
    ) == (
        "## T04 · Project workspace and settings (2026-10-18)\n\nNo progress note from the agent.\n"
    )


def test_entry_with_a_note() -> None:
    entry = format_progress_entry("T04", "Workspace", "Added it.", date(2026, 1, 2))
    assert entry == "## T04 · Workspace (2026-01-02)\n\nAdded it.\n"
