"""The built-in file-size gate."""

from pathlib import Path

import pytest

from spoolhq.services.gates import (
    DEFAULT_EXEMPT,
    FILE_SIZE,
    GateStatus,
    check_file_sizes,
    is_exempt,
)


def lines(count: int) -> str:
    return "".join(f"x{i} = {i}\n" for i in range(count))


def check(repo: Path, files: dict[str, str | bytes], old: str | None = None, limit: int = 500):
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8") if isinstance(content, str) else content
        path.write_bytes(data)
    before = None if old is None else old.encode("utf-8")
    return check_file_sizes(repo, [(name, before) for name in files], limit)


def test_a_new_file_over_the_limit_fails(tmp_path: Path) -> None:
    result = check(tmp_path, {"src/big.py": lines(600)})
    assert (result.name, result.status) == (FILE_SIZE, GateStatus.FAILED)
    assert result.excerpt == "src/big.py: 600 lines, over the 500-line limit"
    assert result.command == "max 500 lines per file"
    assert result.exit_code is None


def test_a_file_at_the_limit_passes(tmp_path: Path) -> None:
    assert check(tmp_path, {"ok.py": lines(500)}).status is GateStatus.PASSED


def test_a_file_already_over_the_limit_may_not_grow(tmp_path: Path) -> None:
    result = check(tmp_path, {"old.py": lines(655)}, old=lines(640))
    assert result.status is GateStatus.FAILED
    assert result.excerpt == "old.py grew from 640 to 655 lines; it was already over the limit"


@pytest.mark.parametrize("after", [630, 640])
def test_a_file_already_over_the_limit_may_shrink_or_stay(tmp_path: Path, after: int) -> None:
    assert check(tmp_path, {"old.py": lines(after)}, old=lines(640)).status is GateStatus.PASSED


def test_a_file_that_was_within_the_limit_may_not_cross_it(tmp_path: Path) -> None:
    result = check(tmp_path, {"f.py": lines(501)}, old=lines(400))
    assert result.excerpt == "f.py: 501 lines, over the 500-line limit"


@pytest.mark.parametrize(
    "name", ["uv.lock", "frontend/pnpm-lock.yaml", "package-lock.json", "static/app.min.js"]
)
def test_lockfiles_and_minified_files_are_exempt(tmp_path: Path, name: str) -> None:
    assert check(tmp_path, {name: lines(900)}).status is GateStatus.PASSED


def test_a_custom_exempt_list_replaces_the_default(tmp_path: Path) -> None:
    (tmp_path / "gen").mkdir()
    (tmp_path / "gen" / "api.ts").write_text(lines(900), encoding="utf-8")
    (tmp_path / "uv.lock").write_text(lines(900), encoding="utf-8")
    changed = [("gen/api.ts", None), ("uv.lock", None)]
    result = check_file_sizes(tmp_path, changed, 500, ["gen/**"])
    assert result.excerpt == "uv.lock: 900 lines, over the 500-line limit"


def test_zero_turns_it_off(tmp_path: Path) -> None:
    result = check(tmp_path, {"big.py": lines(9000)}, limit=0)
    assert (result.status, result.command, result.excerpt) == (GateStatus.SKIPPED, "", "")


def test_a_binary_file_is_skipped(tmp_path: Path) -> None:
    assert check(tmp_path, {"logo.png": b"\0\n" * 900}).status is GateStatus.PASSED


def test_every_problem_is_listed(tmp_path: Path) -> None:
    result = check(tmp_path, {"a.py": lines(501), "b.py": lines(502)})
    assert result.excerpt.splitlines() == [
        "a.py: 501 lines, over the 500-line limit",
        "b.py: 502 lines, over the 500-line limit",
    ]


def test_lines_are_counted_like_the_line_limit_script(tmp_path: Path) -> None:
    # splitlines: no trailing newline still counts the last line, \r\n is one break.
    assert check(tmp_path, {"a.py": "x\r\n" * 500 + "y"}).status is GateStatus.FAILED
    assert check(tmp_path, {"b.py": "x\r\n" * 500}).status is GateStatus.PASSED


def test_a_deleted_or_symlinked_path_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "big.py").write_text(lines(900), encoding="utf-8")
    link = tmp_path / "link.py"
    try:
        link.symlink_to(tmp_path / "big.py")
    except OSError:
        pytest.skip("symlinks need privileges here")
    result = check_file_sizes(tmp_path, [("link.py", None), ("gone.py", None)], 500)
    assert result.status is GateStatus.PASSED


def test_top_level_matches_for_double_star_patterns() -> None:
    assert is_exempt("uv.lock", DEFAULT_EXEMPT)
    assert is_exempt("a/b/Cargo.lock", DEFAULT_EXEMPT)
    assert not is_exempt("src/lock.py", DEFAULT_EXEMPT)
