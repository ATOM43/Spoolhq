"""The fastapi-react template's notes layout, without installing anything."""

from pathlib import Path

from spoolhq.services.notes import END, START, convert_notes, notes_problems
from spoolhq.services.templates import open_template, render


def test_a_generated_project_starts_in_the_split_layout(tmp_path: Path) -> None:
    repo = tmp_path / "demo"
    with open_template("fastapi-react") as template:
        render(template, repo, "demo")
    progress = (repo / "PROGRESS.md").read_text(encoding="utf-8")
    assert progress.startswith("# Progress\n\n## What exists\n")
    assert progress.endswith(f"{START}\n{END}\n")
    decisions = (repo / "DECISIONS.md").read_text(encoding="utf-8")
    assert decisions.startswith("# Decisions\n")
    assert (repo / "docs" / "decisions" / ".gitkeep").is_file()
    # Nothing to convert and nothing to fix before the first ticket.
    assert notes_problems(repo) == []
    assert convert_notes(repo) == ([], [])
    claude = (repo / "CLAUDE.md").read_text(encoding="utf-8")
    assert "go in your run note, never into the notes files" in claude
