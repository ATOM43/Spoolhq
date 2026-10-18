"""``run_gates`` and ``check_done_when`` end to end with ``fake_tool.py``."""

import dataclasses
import time
from pathlib import Path

import pytest

from spoolhq.services.gates import (
    DEFAULT_TIMEOUTS,
    GateResult,
    GateRun,
    GateStatus,
    check_done_when,
    run_gates,
)
from spoolhq.services.gates.output import EXCERPT_CHARS
from tests.conftest import fake_tool_cmd

pytestmark = pytest.mark.integration

PASS = fake_tool_cmd("pass")


def gates(tmp_path: Path, *, install: str = PASS, lint: str = PASS, test: str = PASS) -> GateRun:
    worktree = tmp_path / "wt"
    worktree.mkdir(exist_ok=True)
    return run_gates(
        worktree,
        {"install": install, "lint": lint, "test": test},
        DEFAULT_TIMEOUTS,
        tmp_path / "logs",
    )


def test_all_passing(tmp_path: Path) -> None:
    run = gates(tmp_path)

    assert run.passed
    assert run.first_failure is None
    assert [r.status for r in run.results] == [GateStatus.PASSED] * 3
    assert run.results[2].log_path == tmp_path / "logs" / "test.log"
    assert run.results[2].output_lines == 1
    assert run.to_gate_failures() == ()


def test_failing_test(tmp_path: Path) -> None:
    result = gates(tmp_path, test=fake_tool_cmd("fail-test")).results[2]

    assert result.status is GateStatus.FAILED
    assert result.exit_code == 1
    assert result.failing_tests == ("tests/test_math.py::test_add", "tests/test_math.py::test_sub")
    assert "FAILED tests/test_math.py::test_add - assert 2 == 3" in result.excerpt


def test_lint_error(tmp_path: Path) -> None:
    run = gates(tmp_path, lint=fake_tool_cmd("lint-error"))
    result = run.results[1]

    assert result.status is GateStatus.FAILED
    assert "src/app.py:3:1: error: Name 'x' is not defined  [name-defined]" in result.excerpt
    assert result.failing_tests == ()
    assert run.first_failure is result


def test_timeout(tmp_path: Path) -> None:
    start = time.monotonic()
    run = run_gates(
        tmp_path,
        {"install": PASS, "lint": PASS, "test": fake_tool_cmd("sleep")},
        {**DEFAULT_TIMEOUTS, "test": 1},
        tmp_path / "logs",
    )
    result = run.results[2]

    assert time.monotonic() - start < 10
    assert result.status is GateStatus.TIMED_OUT
    assert result.exit_code is None
    assert run.to_gate_failures() == (
        {
            "command": result.command,
            "exit_code": None,
            "timed_out": True,
            "output_excerpt": "sleeping\n",
        },
    )


def test_fifty_thousand_lines_keep_the_first_failure(tmp_path: Path) -> None:
    result = gates(tmp_path, test=fake_tool_cmd("flood")).results[2]

    assert result.status is GateStatus.FAILED
    assert result.output_lines == 50_002
    assert result.output_truncated is False
    assert len(result.excerpt) <= EXCERPT_CHARS
    assert "FAILED tests/test_big.py::test_first - assert 1 == 2" in result.excerpt
    assert "lines cut …]" in result.excerpt
    assert result.excerpt.endswith("2 failed, 49998 passed")
    assert result.failing_tests == (
        "tests/test_big.py::test_first",
        "tests/test_big.py::test_second",
    )
    assert result.log_path is not None
    log_lines = result.log_path.read_text(encoding="utf-8").split("\n")
    assert len(log_lines) == 50_003 and log_lines[-1] == ""


def test_failing_install_skips_lint_and_test(tmp_path: Path) -> None:
    run = gates(tmp_path, install=fake_tool_cmd("fail-test"))

    assert [r.status for r in run.results] == [
        GateStatus.FAILED,
        GateStatus.SKIPPED,
        GateStatus.SKIPPED,
    ]
    assert run.results[1].log_path is None


def test_failing_lint_still_runs_test(tmp_path: Path) -> None:
    run = gates(tmp_path, lint=fake_tool_cmd("lint-error"), test=fake_tool_cmd("fail-test"))

    assert [r.status for r in run.results] == [
        GateStatus.PASSED,
        GateStatus.FAILED,
        GateStatus.FAILED,
    ]
    assert [f["command"] for f in run.to_gate_failures()] == [
        run.results[1].command,
        run.results[2].command,
    ]


def test_secrets_never_reach_a_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "MY_SECRET", "CLICKUP_API_KEY"):
        monkeypatch.setenv(name, "secret-value")

    result = gates(tmp_path, test=fake_tool_cmd("print-env")).results[2]

    assert result.log_path is not None
    env = result.log_path.read_text(encoding="utf-8")
    assert "secret-value" not in env
    lines = env.splitlines()
    assert "CI=1" in lines
    assert "NO_COLOR=1" in lines


def test_missing_program_is_an_error(tmp_path: Path) -> None:
    run = gates(tmp_path, test="no-such-program-spoolhq test")
    result = run.results[2]

    assert result.status is GateStatus.ERROR
    assert result.excerpt == "gate 'test': program 'no-such-program-spoolhq' not found on PATH"
    assert result.exit_code is None
    assert result.log_path is None
    assert not run.passed
    assert run.first_failure is result
    assert run.to_gate_failures() == ()


def test_shell_syntax_is_an_error_even_unvalidated(tmp_path: Path) -> None:
    result = gates(tmp_path, test="just test && rm -rf /").results[2]

    assert result.status is GateStatus.ERROR
    assert result.excerpt == (
        "gate 'test': shell syntax isn't supported; put it in a justfile recipe"
    )


def test_ansi_and_invalid_utf8_in_the_excerpt(tmp_path: Path) -> None:
    result = gates(tmp_path, test=fake_tool_cmd("ansi")).results[2]

    assert result.excerpt == "FAILED tests/a.py::test_red - boom\nbad � byte\ndone\n"
    assert result.failing_tests == ("tests/a.py::test_red",)


def test_same_worktree_gives_equal_results(tmp_path: Path) -> None:
    def without_duration(run: GateRun) -> list[GateResult]:
        return [dataclasses.replace(r, duration_s=0.0) for r in run.results]

    first = gates(tmp_path, test=fake_tool_cmd("fail-test"))
    second = gates(tmp_path, test=fake_tool_cmd("fail-test"))

    assert without_duration(first) == without_duration(second)


def test_done_when_maps_configured_commands_only(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    test_cmd = fake_tool_cmd("fail-test")
    commands = {"install": PASS, "lint": "just lint", "test": test_cmd}
    run = gates(tmp_path, lint=PASS, test=test_cmd)
    rogue = fake_tool_cmd("marker", str(marker))

    checks = check_done_when(
        [
            f"`{test_cmd}` passes",
            f"`{PASS}` passes on a clean checkout",
            f"`{rogue}` passes",
            "`rm -rf ~` passes",
            "the README mentions `just test`",
            "no command here",
        ],
        commands,
        run,
    )

    assert [(c.command, c.status) for c in checks] == [
        (test_cmd, "failed"),
        (PASS, "passed"),
        (rogue, "not_a_gate"),
        ("rm -rf ~", "not_a_gate"),
    ]
    assert checks[0].item == f"`{test_cmd}` passes"
    assert not marker.exists()


def test_done_when_with_just_test(tmp_path: Path) -> None:
    passing = gates(tmp_path)
    commands = {"install": "just install", "lint": "just lint", "test": "just test"}
    failing = dataclasses.replace(
        passing,
        results=(
            *passing.results[:2],
            dataclasses.replace(passing.results[2], status=GateStatus.FAILED),
        ),
    )

    assert check_done_when(["`just test` passes"], commands, passing)[0].status == "passed"
    assert check_done_when(["`just test` passes"], commands, failing)[0].status == "failed"
