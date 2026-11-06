"""Keep ``tests/`` mirroring ``src/spoolhq/`` (see "Layout" in docs/testing.md), and the
decisions index matching ``docs/decisions/``."""

import importlib.util
from pathlib import Path
from typing import Any

from tests.conftest import FIXTURES_DIR, TESTS_DIR

PACKAGE_DIR = TESTS_DIR.parent / "src" / "spoolhq"


def folders() -> list[Path]:
    """Every folder under ``tests/`` except shared fixture data and caches."""
    return sorted(
        path
        for path in TESTS_DIR.rglob("*")
        if path.is_dir()
        and path != FIXTURES_DIR
        and FIXTURES_DIR not in path.parents
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    )


def test_no_test_files_directly_in_tests() -> None:
    stray = sorted(
        path.name for path in TESTS_DIR.glob("test_*.py") if path.name != Path(__file__).name
    )
    assert stray == [], f"move these into the folder that mirrors the code they test: {stray}"


def test_every_test_folder_mirrors_a_package() -> None:
    unmatched = [
        folder.relative_to(TESTS_DIR).as_posix()
        for folder in folders()
        if not (PACKAGE_DIR / folder.relative_to(TESTS_DIR)).is_dir()
    ]
    assert unmatched == [], f"no matching package under src/spoolhq/ for: {unmatched}"


def test_every_test_folder_has_init() -> None:
    missing = [
        folder.relative_to(TESTS_DIR.parent).as_posix()
        for folder in [TESTS_DIR, *folders()]
        if not (folder / "__init__.py").is_file()
    ]
    assert missing == [], f"add an empty __init__.py to: {missing}"


# DECISIONS.md and docs/decisions/ (scripts/check_decisions.py, run by `just lint`).


def _script(name: str) -> Any:
    path = TESTS_DIR.parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_decisions() -> Any:
    return _script("check_decisions")


def _decisions(root: Path, index: list[str], entries: list[str]) -> Path:
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "DECISIONS.md").write_text("# Decisions\n\n" + "\n".join(index) + "\n", "utf-8")
    (root / "docs" / "decisions" / "core.md").write_text("\n".join(entries) + "\n", "utf-8")
    return root


GOOD_INDEX = ["001 · One · docs/decisions/core.md", "002 · Two. · docs/decisions/core.md"]
GOOD_ENTRIES = ["1. **One** (T01). Why.", "2. **Two.** Why."]


def test_the_repo_decisions_layout_is_consistent() -> None:
    assert _check_decisions().problems(TESTS_DIR.parents[1]) == []


def test_a_consistent_fixture_passes(tmp_path: Path) -> None:
    root = _decisions(tmp_path, GOOD_INDEX, GOOD_ENTRIES)
    assert _check_decisions().problems(root) == []


def test_a_missing_number_fails(tmp_path: Path) -> None:
    index = [GOOD_INDEX[0], "003 · Three · docs/decisions/core.md"]
    entries = [GOOD_ENTRIES[0], "3. **Three** Why."]
    found = _check_decisions().problems(_decisions(tmp_path, index, entries))
    assert found == ["DECISIONS.md: 2 is missing (numbers must have no gaps)"]


def test_an_entry_missing_from_the_area_files_fails(tmp_path: Path) -> None:
    found = _check_decisions().problems(_decisions(tmp_path, GOOD_INDEX, GOOD_ENTRIES[:1]))
    assert found == ["DECISIONS.md: 2 has no entry in docs/decisions/"]


def test_a_duplicated_number_fails(tmp_path: Path) -> None:
    index = [*GOOD_INDEX, GOOD_INDEX[1]]
    entries = [*GOOD_ENTRIES, GOOD_ENTRIES[1]]
    found = _check_decisions().problems(_decisions(tmp_path, index, entries))
    assert "DECISIONS.md: 2 is listed 2 times" in found
    assert "docs/decisions: 2 has 2 entries" in found


def test_a_mismatched_title_fails(tmp_path: Path) -> None:
    index = [GOOD_INDEX[0], "002 · Two · docs/decisions/core.md"]
    found = _check_decisions().problems(_decisions(tmp_path, index, GOOD_ENTRIES))
    assert found == ["DECISIONS.md: 2 title 'Two' != heading 'Two.'"]


# The 500-line limit (scripts/check_line_limit.py, run by `just lint`).


def test_the_repo_is_within_the_line_limit() -> None:
    assert _script("check_line_limit").oversized(TESTS_DIR.parents[1]) == []


def test_a_rust_file_over_the_limit_fails(tmp_path: Path) -> None:
    folder = tmp_path / "desktop" / "src-tauri" / "src"
    folder.mkdir(parents=True)
    (folder / "short.rs").write_text("fn a() {}\n" * 500, encoding="utf-8")
    (folder / "long.rs").write_text("fn a() {}\n" * 501, encoding="utf-8")
    found = _script("check_line_limit").oversized(tmp_path)
    assert found == [("desktop/src-tauri/src/long.rs", 501)]
