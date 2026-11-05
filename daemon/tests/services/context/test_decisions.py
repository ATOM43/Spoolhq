"""services/context: reading DECISIONS.md as a full log or as an index of area files."""

import logging
import os
import shutil
from pathlib import Path

import pytest

from spoolhq.services.context import build_implementer_prompt, read_repo_docs
from tests.services.context.conftest import (
    CONTEXT_FIXTURES,
    EXPECTED_DIR,
    block,
    fixture_inputs,
    read_text,
)

AREA = "docs/decisions/core.md"


def entry(number: int) -> str:
    return f"{number}. **Decision {number}** (T{number:02d}). Because reason {number}."


def write_split(repo: Path, numbers: range, *, area: str = AREA) -> None:
    (repo / "docs" / "decisions").mkdir(parents=True, exist_ok=True)
    index = [f"{n:03d} · Decision {n} · {area}" for n in numbers]
    (repo / "DECISIONS.md").write_text("# Decisions\n\nHow to use.\n\n" + "\n".join(index) + "\n")
    (repo / area).write_text("# Core\n\n" + "\n".join(entry(n) for n in numbers) + "\n")


def decisions_block(repo: Path) -> str:
    docs = read_repo_docs(repo, 20)
    fenced = block(build_implementer_prompt(fixture_inputs(repo_docs=docs)).text, "decisions")
    lines = fenced.splitlines()
    assert lines[0] == lines[-1] == "```"
    return "\n".join(lines[1:-1])


def test_split_layout_gives_the_last_20_entries_in_full_and_in_order(tmp_path: Path) -> None:
    write_split(tmp_path, range(1, 26))
    # Entries spread over two area files, listed in number order in the index.
    other = "docs/decisions/agents.md"
    (tmp_path / other).write_text(entry(26) + "\n  continued on an indented line.\n\nNot part.\n")
    with (tmp_path / "DECISIONS.md").open("a") as file:
        file.write(f"026 · Decision 26 · {other}\n")

    text = decisions_block(tmp_path)

    expected = [entry(n) for n in range(7, 26)] + [entry(26), "  continued on an indented line."]
    assert text.splitlines() == expected
    assert "Decision 6" not in text and "Not part." not in text


def test_entries_follow_number_order_not_index_order(tmp_path: Path) -> None:
    write_split(tmp_path, range(1, 4))
    index = tmp_path / "DECISIONS.md"
    index.write_text("\n".join(reversed(index.read_text().splitlines())) + "\n")

    docs = read_repo_docs(tmp_path, 2)

    assert docs.decisions_selected
    assert docs.decisions_md == f"{entry(2)}\n{entry(3)}\n"


def test_single_file_layout_renders_byte_identical_to_the_snapshot(tmp_path: Path) -> None:
    for name in ("CLAUDE.md", "PROGRESS.md", "DECISIONS.md"):
        shutil.copyfile(CONTEXT_FIXTURES / name, tmp_path / name)

    docs = read_repo_docs(tmp_path, 20)
    prompt = build_implementer_prompt(fixture_inputs(repo_docs=docs))

    assert not docs.decisions_selected
    assert docs.decisions_md == read_text(CONTEXT_FIXTURES / "DECISIONS.md")
    # implementer_initial.md was recorded before this change.
    assert prompt.text == read_text(EXPECTED_DIR / "implementer_initial.md")


def test_missing_notes_are_none(tmp_path: Path) -> None:
    docs = read_repo_docs(tmp_path, 20)
    assert (docs.claude_md, docs.progress_md, docs.decisions_md) == (None, None, None)


def test_missing_area_file_and_entry_keep_the_title_with_one_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    write_split(tmp_path, range(1, 4))
    with (tmp_path / "DECISIONS.md").open("a") as file:
        file.write("004 · Decision 4 · docs/decisions/gone.md\n")
    (tmp_path / AREA).write_text(entry(1) + "\n" + entry(3) + "\n")  # 2 is missing

    with caplog.at_level(logging.WARNING):
        docs = read_repo_docs(tmp_path, 20)

    assert docs.decisions_md == (
        f"{entry(1)}\n002 · Decision 2 · {AREA}\n{entry(3)}\n"
        "004 · Decision 4 · docs/decisions/gone.md\n"
    )
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "2 (docs/decisions/core.md), 4 (docs/decisions/gone.md)" in warnings[0].getMessage()


def outside_paths(repo: Path, secret: Path) -> list[str]:
    paths = ["../secret.md", str(secret), "docs\\..\\..\\secret.md", "C:secret.md"]
    link = repo / "docs" / "link.md"
    try:
        os.symlink(secret, link)
    except OSError:  # Windows without the symlink privilege
        return paths
    return [*paths, "docs/link.md"]


def test_paths_outside_the_repo_are_never_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    write_split(repo, range(1, 2))
    secret = tmp_path / "secret.md"
    secret.write_text("1. **Secret** do not read.\n")
    paths = outside_paths(repo, secret)
    index = "".join(f"{n:03d} · Decision {n} · {p}\n" for n, p in enumerate(paths, start=2))
    with (repo / "DECISIONS.md").open("a") as file:
        file.write(index)

    read: list[Path] = []
    original = Path.read_text

    def spy(self: Path, *args: object, **kwargs: object) -> str:
        read.append(self.resolve())
        return original(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", spy)
    docs = read_repo_docs(repo, 20)

    assert secret.resolve() not in read
    assert docs.decisions_md is not None and "Secret" not in docs.decisions_md
    assert docs.decisions_md.splitlines()[0] == entry(1)
    assert docs.decisions_md.splitlines()[1:] == index.splitlines()
