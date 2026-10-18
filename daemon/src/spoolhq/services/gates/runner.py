"""Run a project's install, lint and test gates in a worktree, and check "Done when" items."""

import os
import re
import sys
import time
from collections.abc import Iterable, Mapping
from pathlib import Path

from spoolhq.services.gates.command import gate_env, resolve_program, split_command
from spoolhq.services.gates.model import (
    GATE_NAMES,
    DoneWhenCheck,
    GateName,
    GateResult,
    GateRun,
    GateStatus,
)
from spoolhq.services.gates.output import build_excerpt, clean, failing_tests
from spoolhq.services.gates.process import OUTPUT_CAP_BYTES, run_process

# Seconds; project.yaml's gates.timeouts defaults.
DEFAULT_TIMEOUTS: dict[GateName, int] = {"install": 600, "lint": 300, "test": 900}
# "`just test` passes": a backticked command followed by the word "passes".
_DONE_WHEN_RE = re.compile(r"`([^`]+)`\s+passes\b")


def run_gates(
    worktree: Path,
    commands: Mapping[str, str],
    timeouts: Mapping[str, float],
    log_dir: Path,
    *,
    cap_bytes: int = OUTPUT_CAP_BYTES,
) -> GateRun:
    """Run install, lint and test in ``worktree``; each gate's output goes to
    ``<log_dir>/<gate>.log``.

    If install doesn't pass, lint and test are skipped. Lint and test both run even
    if lint fails, so one retry sees every error.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    env = gate_env(os.environ, platform=sys.platform)
    results: list[GateResult] = []
    for name in GATE_NAMES:
        command = commands[name]
        if results and results[0].status is not GateStatus.PASSED:
            results.append(_not_run(name, command, GateStatus.SKIPPED, ""))
            continue
        results.append(
            _run_gate(
                name,
                command,
                worktree=worktree,
                env=env,
                timeout_s=timeouts[name],
                log_path=log_dir / f"{name}.log",
                cap_bytes=cap_bytes,
            )
        )
    return GateRun(tuple(results))


def _not_run(name: GateName, command: str, status: GateStatus, message: str) -> GateResult:
    return GateResult(name, command, status, None, 0.0, message, (), 0, False, None)


def _run_gate(
    name: GateName,
    command: str,
    *,
    worktree: Path,
    env: Mapping[str, str],
    timeout_s: float,
    log_path: Path,
    cap_bytes: int,
) -> GateResult:
    try:
        argv = split_command(command)
    except ValueError as exc:
        return _not_run(name, command, GateStatus.ERROR, f"gate '{name}': {exc}")
    program = resolve_program(argv[0], env)
    if program is None:
        message = f"gate '{name}': program '{argv[0]}' not found on PATH"
        return _not_run(name, command, GateStatus.ERROR, message)

    start = time.monotonic()
    try:
        result = run_process(
            [program, *argv[1:]],
            cwd=worktree,
            env=env,
            timeout_s=timeout_s,
            log_path=log_path,
            cap_bytes=cap_bytes,
        )
    except OSError as exc:
        message = f"gate '{name}': couldn't start '{argv[0]}': {exc.strerror or exc}"
        return _not_run(name, command, GateStatus.ERROR, message)
    duration = time.monotonic() - start

    if result.timed_out:
        status = GateStatus.TIMED_OUT
    elif result.exit_code == 0:
        status = GateStatus.PASSED
    else:
        status = GateStatus.FAILED
    excerpt = ""
    tests: tuple[str, ...] = ()
    if status is not GateStatus.PASSED:
        # The log is at most the cap (20 MB) plus the cut line.
        output = clean(log_path.read_bytes().decode("utf-8", errors="replace"))
        excerpt, tests = build_excerpt(output), failing_tests(output)
    return GateResult(
        name=name,
        command=command,
        status=status,
        exit_code=result.exit_code,
        duration_s=duration,
        excerpt=excerpt,
        failing_tests=tests,
        output_lines=result.output_lines,
        output_truncated=result.output_truncated,
        log_path=log_path,
    )


def check_done_when(
    done_when_lines: Iterable[str], commands: Mapping[str, str], run: GateRun
) -> tuple[DoneWhenCheck, ...]:
    """Map items like `` `just test` passes `` to that gate's result.

    Only a backticked command equal to a configured one counts; any other is reported
    as ``not_a_gate`` and never run, because ticket text is untrusted. Items without a
    backticked command followed by "passes" are left out.
    """
    by_command = {command: name for name, command in reversed(list(commands.items()))}
    statuses: dict[str, GateStatus] = {result.name: result.status for result in run.results}
    checks: list[DoneWhenCheck] = []
    for item in done_when_lines:
        match = _DONE_WHEN_RE.search(item)
        if match is None:
            continue
        command = match[1]
        name = by_command.get(command)
        if name is None:
            checks.append(DoneWhenCheck(item, command, "not_a_gate"))
        else:
            passed = statuses.get(name) is GateStatus.PASSED
            checks.append(DoneWhenCheck(item, command, "passed" if passed else "failed"))
    return tuple(checks)
