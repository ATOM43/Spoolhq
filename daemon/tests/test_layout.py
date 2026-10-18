"""Keep ``tests/`` mirroring ``src/spoolhq/``; see "Layout" in docs/testing.md."""

from pathlib import Path

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
