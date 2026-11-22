"""The test guard: deleted, removed, skipped or focused tests fail unless a "Done when"
item names them; coverage may fall at most half a point."""

from pathlib import Path

import pytest

from spoolhq.services.gates import (
    DEFAULT_TEST_PATHS,
    Coverage,
    FileChange,
    GateStatus,
    check_tests,
)

PY = "def test_limit_at_50hz():\n    pass\n\n\ndef test_other():\n    pass\n"
JS = 'it("adds two", () => {});\ntest("keeps one", () => {});\n'


def guard(
    tmp_path: Path,
    changes: list[FileChange],
    done_when: tuple[str, ...] = (),
    coverage: Coverage | None = None,
) -> tuple[GateStatus, str]:
    result = check_tests(tmp_path, changes, DEFAULT_TEST_PATHS, done_when, coverage or Coverage())
    return result.status, result.excerpt


def changed(tmp_path: Path, path: str, before: str | None, after: str) -> FileChange:
    """``path`` now holds ``after``; its added lines are those not in ``before``."""
    (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / path).write_text(after, encoding="utf-8")
    old = (before or "").splitlines()
    added = tuple(
        (number, line) for number, line in enumerate(after.splitlines(), start=1) if line not in old
    )
    return FileChange(path, None if before is None else before.encode(), added=added)


def test_a_deleted_test_file_fails(tmp_path: Path) -> None:
    change = FileChange("backend/tests/test_review.py", PY.encode(), deleted=True)
    status, text = guard(tmp_path, [change])
    assert status is GateStatus.FAILED
    assert text.startswith("Deleted test file backend/tests/test_review.py")


def test_a_removed_python_test_fails_with_its_name(tmp_path: Path) -> None:
    after = "def test_other():\n    pass\n"
    status, text = guard(tmp_path, [changed(tmp_path, "backend/tests/test_review.py", PY, after)])
    assert status is GateStatus.FAILED
    assert "Removed test test_limit_at_50hz in backend/tests/test_review.py" in text


def test_a_removed_js_test_fails(tmp_path: Path) -> None:
    after = 'test("keeps one", () => {});\n'
    status, text = guard(tmp_path, [changed(tmp_path, "src/sum.test.ts", JS, after)])
    assert status is GateStatus.FAILED
    assert "Removed test adds two in src/sum.test.ts" in text


@pytest.mark.parametrize(
    ("path", "before", "after", "marker"),
    [
        ("tests/test_a.py", PY, "import pytest\n@pytest.mark.skip\n" + PY, "pytest.mark.skip"),
        ("src/sum.test.ts", JS, JS.replace('it("adds', 'it.only("adds'), ".only("),
        ("src/sum.spec.js", JS, JS.replace('it("adds', 'xit("adds'), "xit("),
    ],
)
def test_an_added_skip_or_focus_marker_fails(
    tmp_path: Path, path: str, before: str, after: str, marker: str
) -> None:
    status, text = guard(tmp_path, [changed(tmp_path, path, before, after)])
    assert status is GateStatus.FAILED
    assert f"Added {marker} in {path}:" in text


def test_a_skip_marker_names_its_test(tmp_path: Path) -> None:
    after = "import pytest\n@pytest.mark.skip\n" + PY
    _, text = guard(tmp_path, [changed(tmp_path, "tests/test_a.py", PY, after)])
    assert text == "Added pytest.mark.skip in tests/test_a.py:2 (test_limit_at_50hz)"


@pytest.mark.parametrize(
    "item",
    ["Remove `test_limit_at_50hz`, it tests the old limit", "Delete backend/tests/test_review.py"],
)
def test_the_same_removal_passes_when_done_when_names_it(tmp_path: Path, item: str) -> None:
    after = "def test_other():\n    pass\n"
    removed = changed(tmp_path, "backend/tests/test_review.py", PY, after)
    assert guard(tmp_path, [removed], (item,))[0] is GateStatus.PASSED


def test_a_deleted_file_passes_when_done_when_names_it(tmp_path: Path) -> None:
    change = FileChange("backend/tests/test_review.py", PY.encode(), deleted=True)
    named = ("Remove backend/tests/test_review.py",)
    assert guard(tmp_path, [change], named)[0] is GateStatus.PASSED
    assert guard(tmp_path, [change], ("Remove tests/test_review.py",))[0] is GateStatus.FAILED


def test_a_skip_passes_when_done_when_names_the_test(tmp_path: Path) -> None:
    after = "import pytest\n@pytest.mark.skip\n" + PY
    change = changed(tmp_path, "tests/test_a.py", PY, after)
    assert guard(tmp_path, [change], ("Skip test_limit_at_50hz until T12",))[0] is GateStatus.PASSED


def test_renaming_a_test_file_without_removing_tests_passes(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_new.py").write_text(PY, encoding="utf-8")
    rename = FileChange("tests/test_new.py", PY.encode(), old_path="tests/test_old.py")
    assert guard(tmp_path, [rename])[0] is GateStatus.PASSED


def test_non_test_files_are_ignored(tmp_path: Path) -> None:
    change = changed(tmp_path, "src/stream.py", PY, "x = it.skip(3)\n")
    assert guard(tmp_path, [change])[0] is GateStatus.PASSED


def test_coverage_more_than_half_a_point_down_fails(tmp_path: Path) -> None:
    status, text = guard(tmp_path, [], coverage=Coverage(88.4, 91.2))
    assert status is GateStatus.FAILED
    assert text == "Coverage fell from 91.2% to 88.4%"


def test_coverage_within_half_a_point_passes(tmp_path: Path) -> None:
    assert guard(tmp_path, [], coverage=Coverage(90.9, 91.2)) == (
        GateStatus.PASSED,
        "Coverage 90.9% (main 91.2%)",
    )
    assert guard(tmp_path, [], coverage=Coverage(90.7, 91.2))[0] is GateStatus.PASSED


def test_a_skipped_coverage_check_says_why(tmp_path: Path) -> None:
    note = "Coverage not compared: no gates.coverage_report in project.yaml"
    assert guard(tmp_path, [], coverage=Coverage(note=note)) == (GateStatus.PASSED, note)


def test_a_coverage_problem_fails_the_guard(tmp_path: Path) -> None:
    problem = "Coverage report coverage.xml wasn't written; the test command must write it"
    coverage = Coverage(stored=91.2, problem=problem)
    assert guard(tmp_path, [], coverage=coverage) == (GateStatus.FAILED, problem)
