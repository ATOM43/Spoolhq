"""Cleaning output, the first failure, the excerpt and failing test names."""

from spoolhq.services.gates.output import (
    EXCERPT_CHARS,
    build_excerpt,
    clean,
    failing_tests,
    first_failure,
)


def test_clean_strips_ansi_and_crlf() -> None:
    text = "\x1b[1;31mred\x1b[0m\r\n\x1b]0;title\x07plain\r\n\x1b(Bdone"
    assert clean(text) == "red\nplain\ndone"


def test_failed_line_wins_over_an_earlier_error() -> None:
    lines = ["warning", "error: something", "Traceback (most recent call last)", "FAILED t::x"]
    assert first_failure(lines) == 3


def test_priorities_in_order() -> None:
    assert first_failure(["x: error: a", "Traceback (most recent call last):"]) == 1
    assert first_failure(["error: a", " FAIL  src/a.test.ts > adds"]) == 1
    assert first_failure(["error: a", "src/a.ts(1,2): error TS2304: no"]) == 1
    assert first_failure(["error: a", "error[E0425]: cannot find"]) == 1
    assert first_failure(["ok", "boom error: a"]) == 1
    assert first_failure(["Error: case matters", "fine"]) is None


def test_output_that_fits_is_unchanged() -> None:
    text = "a\r\nb\n\n  c  \n"
    assert build_excerpt(text) == text


def test_excerpt_keeps_head_failure_window_and_tail() -> None:
    lines = [f"line {n}" for n in range(3_000)]
    lines[1_500] = "FAILED tests/t.py::test_x - assert False"
    excerpt = build_excerpt("\n".join(lines) + "\n")

    assert len(excerpt) <= EXCERPT_CHARS
    parts = excerpt.split("\n")
    assert parts[:20] == lines[:20]
    assert parts[20].startswith("[… ") and parts[20].endswith(" lines cut …]")
    assert parts[21:52] == lines[1_470:1_501]  # 30 lines before the failure, then it
    assert parts[-40:] == lines[-40:]
    assert sum(1 for part in parts if "lines cut" in part) == 2


def test_excerpt_without_failure_is_head_and_tail() -> None:
    lines = [f"line {n}" for n in range(3_000)]
    parts = build_excerpt("\n".join(lines)).split("\n")
    assert parts == [*lines[:20], "[… 2940 lines cut …]", *lines[-40:]]


def test_excerpt_with_huge_lines_stays_under_the_limit() -> None:
    lines = ["x" * 5_000] * 200
    lines[100] = "FAILED t::big " + "y" * 5_000
    excerpt = build_excerpt("\n".join(lines))
    assert len(excerpt) <= EXCERPT_CHARS
    assert "FAILED t::big" in excerpt


def test_failure_in_the_head_needs_no_window() -> None:
    lines = [f"line {n}" for n in range(3_000)]
    lines[5] = "error: early"
    parts = build_excerpt("\n".join(lines)).split("\n")
    assert parts[5] == "error: early"
    assert sum(1 for part in parts if "lines cut" in part) == 1


def test_failing_tests_pytest_and_vitest() -> None:
    text = "\n".join(
        [
            "FAILED tests/test_math.py::test_add - assert 2 == 3",
            "ERROR tests/test_db.py::test_conn",
            "FAILED tests/test_p.py::test_x[a - b] - boom",
            " FAIL  src/a.test.ts > adds",
            "FAIL src/b.test.ts > group > subtracts",
            " FAIL  src/c.test.ts [ src/c.test.ts ]",
            "FAILED tests/test_math.py::test_add - assert 2 == 3",
            "  FAILED indented is not a summary line",
        ]
    )
    assert failing_tests(text) == (
        "tests/test_math.py::test_add",
        "tests/test_db.py::test_conn",
        "tests/test_p.py::test_x[a",
        "src/a.test.ts > adds",
        "src/b.test.ts > group > subtracts",
    )


def test_other_tools_give_no_failing_tests() -> None:
    assert failing_tests("error[E0425]: cannot find value\n✗ broken\n") == ()
