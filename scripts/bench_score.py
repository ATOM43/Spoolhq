"""Score an app against a benchmark and write a markdown summary (docs/benchmarks/README.md).

    just bench-score <app> <adapter> <suite> [--project NAME] [--out FILE]
        [--lint CMD] [--test CMD] [--coverage CMD]

It works on a temporary copy of the app folder, so the app itself is never written to:
the hidden suite through the adapter (pytest in the suite's own uv project), the app's
own lint and test commands (its `just` or `make` targets unless given), an optional
coverage command, and SpoolHQ's file-size gate over the app's tracked files. With
`--project`, it also reads that SpoolHQ project's run log for the process numbers.
Nothing here knows about any one benchmark.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from spoolhq.core.config import load_settings
from spoolhq.services.gates import DEFAULT_MAX_FILE_LINES, check_file_sizes, split_command
from spoolhq.services.runs.db import connect

TIMEOUT_S = 1800
TAIL_LINES = 15
SUITE = "hidden suite"
VERDICTS = ("approved", "changes_requested", "needs_human")


@dataclass(frozen=True)
class Case:
    name: str
    outcome: str
    """passed, failed, error or skipped."""
    reqs: tuple[str, ...] = ()
    props: dict[str, str] = field(default_factory=dict)


def read_junit(path: Path) -> list[Case]:
    """Each test case of a pytest JUnit report, with its `req` ids and other properties."""
    cases = []
    root = ET.parse(path).getroot()  # noqa: S314 (the report our own pytest run wrote)
    for case in root.iter("testcase"):
        tags = {child.tag for child in case}
        outcome = next((t for t in ("error", "failure", "skipped") if t in tags), "passed")
        props = {p.get("name", ""): p.get("value", "") for p in case.iter("property")}
        reqs = tuple(r for r in props.pop("req", "").split(",") if r)
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        cases.append(Case(name, "failed" if outcome == "failure" else outcome, reqs, props))
    return cases


def by_requirement(cases: Sequence[Case]) -> dict[str, tuple[int, int]]:
    """Requirement id → (tests passed, tests), in id order (R2 before R10)."""
    passed: Counter[str] = Counter()
    total: Counter[str] = Counter()
    for case in cases:
        for req in case.reqs:
            total[req] += 1
            passed[req] += case.outcome == "passed"
    return {r: (passed[r], total[r]) for r in sorted(total, key=lambda r: (len(r), r))}


@dataclass(frozen=True)
class Check:
    name: str
    command: str
    ok: bool
    seconds: float
    output: str


def run(name: str, argv: Sequence[str], cwd: Path, env: dict[str, str] | None = None) -> Check:
    """Run `argv` (no shell); a missing program or a timeout is a failed check."""
    started = time.monotonic()
    child_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **(env or {})}
    child_env.pop("VIRTUAL_ENV", None)
    try:
        done = subprocess.run(  # noqa: S603 (an argument list, no shell)
            list(argv),
            cwd=cwd,
            env=child_env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=TIMEOUT_S,
            check=False,
        )
        ok, output = done.returncode == 0, done.stdout + done.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        ok, output = False, str(exc)
    return Check(name, " ".join(argv), ok, time.monotonic() - started, output)


def default_command(app: Path, target: str) -> list[str] | None:
    if (app / "justfile").is_file() or (app / "Justfile").is_file():
        return ["just", target]
    if (app / "Makefile").is_file():
        return ["make", target]
    return None


def coverage_percent(output: str) -> float | None:
    """The first `TOTAL … NN%` line of a coverage.py report."""
    # shortcut: coverage.py's terminal report only; add other formats when an app needs them.
    for line in output.splitlines():
        parts = line.split()
        if parts and parts[0] == "TOTAL" and parts[-1].endswith("%"):
            return float(parts[-1].rstrip("%"))
    return None


def file_sizes(app: Path, limit: int = DEFAULT_MAX_FILE_LINES) -> tuple[int, list[str]] | None:
    """(tracked files, problems) from SpoolHQ's file-size gate; None outside a git repo."""
    listing = run("files", ["git", "ls-files", "-z"], app)
    if not listing.ok:
        return None
    paths = [p for p in listing.output.split("\0") if p]
    result = check_file_sizes(app, [(p, None) for p in paths], limit)
    return len(paths), [line for line in result.excerpt.splitlines() if line]


@dataclass(frozen=True)
class Process:
    tickets: int
    done: int
    first_try: int
    """Done tickets whose only attempt was approved."""
    retries: dict[str, int]
    """Ticket id → attempts after the first."""
    verdicts: dict[str, int]
    blocked: list[str]
    approvals: int
    unblocks: int
    rejections: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cost_usd: float | None
    run_seconds: float
    wall_seconds: float


def _seconds(start: str, end: str) -> float:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def process_numbers(workspace: Path) -> Process:
    """A SpoolHQ project's run log: ticket runs, plus the planner's tokens and time."""
    conn = connect(workspace, read_only=True)
    try:
        runs = conn.execute("SELECT id, ticket_id, kind, status FROM runs").fetchall()
        kind_of = {run_id: (ticket, kind) for run_id, ticket, kind, _ in runs}
        attempts: dict[str, list[str]] = {}
        for run_id, status in conn.execute("SELECT run_id, status FROM attempts ORDER BY id"):
            ticket, kind = kind_of[run_id]
            if kind == "ticket":
                attempts.setdefault(ticket, []).append(status)
        blocked: set[str] = set()
        messages: Counter[str] = Counter()
        for run_id, kind, payload in conn.execute("SELECT run_id, kind, payload FROM events"):
            ticket, run_kind = kind_of[run_id]
            data = json.loads(payload)
            if run_kind != "ticket" or not isinstance(data, dict):
                continue
            if kind == "run.status" and data.get("to") == "blocked":
                blocked.add(ticket)
            elif kind == "log" and isinstance(data.get("message"), str):
                messages[data["message"]] += 1
        tokens = conn.execute(
            "SELECT COALESCE(SUM(input_tokens), 0), COALESCE(SUM(output_tokens), 0),"
            " COALESCE(SUM(cache_read_tokens), 0), SUM(cost_micro_usd) FROM attempts"
        ).fetchone()
        spans = conn.execute("SELECT started_at, ended_at FROM runs WHERE ended_at IS NOT NULL")
        spans_list: list[tuple[str, str]] = spans.fetchall()
    finally:
        conn.close()
    tickets = sorted({ticket for _, ticket, kind, _ in runs if kind == "ticket"})
    done = {ticket for _, ticket, kind, status in runs if kind == "ticket" and status == "done"}
    return Process(
        tickets=len(tickets),
        done=len(done),
        first_try=sum(1 for t in done if attempts.get(t) == ["approved"]),
        retries={t: max(len(attempts.get(t, [])) - 1, 0) for t in tickets},
        verdicts=dict(Counter(s for st in attempts.values() for s in st if s in VERDICTS)),
        blocked=sorted(blocked),
        approvals=messages["approved by the user"],
        unblocks=messages["unblocked by the user"],
        rejections=messages["rejected by the user"],
        input_tokens=tokens[0],
        output_tokens=tokens[1],
        cache_read_tokens=tokens[2],
        cost_usd=None if tokens[3] is None else tokens[3] / 1_000_000,
        run_seconds=sum(_seconds(s, e) for s, e in spans_list),
        wall_seconds=(
            _seconds(min(s for s, _ in spans_list), max(e for _, e in spans_list))
            if spans_list
            else 0.0
        ),
    )


def suite_command(suite: Path, junit: Path) -> tuple[list[str], Path]:
    """pytest in the suite's own uv project (the nearest pyproject.toml above it)."""
    args = ["pytest", str(suite), "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
    args += ["-o", "junit_family=xunit1"]  # xunit2 drops the test properties
    for folder in (suite, *suite.parents):
        if (folder / "pyproject.toml").is_file():
            return ["uv", "run", "--project", str(folder), *args], folder
    return [sys.executable, "-m", *args], suite


def _tail(text: str) -> str:
    return "\n".join(text.strip().splitlines()[-TAIL_LINES:])


def _minutes(seconds: float) -> str:
    return f"{seconds / 60:.1f} min"


def render(
    app: str,
    cases: Sequence[Case],
    checks: Sequence[Check],
    coverage: float | None,
    sizes: tuple[int, list[str]] | None,
    process: Process | None,
) -> str:
    passed = sum(c.outcome == "passed" for c in cases)
    counts = Counter(c.outcome for c in cases)
    rate = f"{100 * passed / len(cases):.1f}%" if cases else "n/a"
    out = [f"# Benchmark score · {app}", ""]
    out += [
        f"**Hidden suite: {passed} of {len(cases)} tests passed ({rate})**; "
        + ", ".join(f"{counts[k]} {k}" for k in ("failed", "error", "skipped")),
        "",
        "## Requirements",
        "",
        "| Requirement | Passed | Tests |",
        "| --- | --- | --- |",
    ]
    out += [f"| {r} | {p} | {t} |" for r, (p, t) in by_requirement(cases).items()]
    measures = {k: v for c in cases for k, v in c.props.items()}
    if measures:
        out += ["", "## Measurements", "", "| Name | Value |", "| --- | --- |"]
        out += [f"| {k} | {v} |" for k, v in sorted(measures.items())]
    out += ["", "## Code health", "", "| Check | Result | Time | Command |"]
    out.append("| --- | --- | --- | --- |")
    health = [c for c in checks if c.name != SUITE]
    out += [
        f"| {c.name} | {'pass' if c.ok else 'FAIL'} | {c.seconds:.1f} s | `{c.command}` |"
        for c in health
    ]
    out += ["", f"- Coverage: {'n/a' if coverage is None else f'{coverage:g}%'}"]
    if sizes is None:
        out.append("- File sizes: n/a (not a git repo)")
    else:
        files, problems = sizes
        out.append(f"- Files over {DEFAULT_MAX_FILE_LINES} lines: {len(problems)} of {files}")
        out += [f"  - {p}" for p in problems]
    if process is not None:
        p = process
        cost = "n/a" if p.cost_usd is None else f"${p.cost_usd:.2f}"
        retried = ", ".join(f"{t} {n}" for t, n in p.retries.items() if n) or "none"
        out += [
            "",
            "## Process",
            "",
            f"- Tickets: {p.tickets} run, {p.done} done, {p.first_try} passed first try",
            f"- Retries: {sum(p.retries.values())} ({retried})",
            "- Review verdicts: "
            + (", ".join(f"{k} {v}" for k, v in sorted(p.verdicts.items())) or "none"),
            f"- Blocked tickets: {len(p.blocked)} ({', '.join(p.blocked) or 'none'})",
            f"- User approvals: {p.approvals}; unblocks: {p.unblocks}; rejections: {p.rejections}",
            f"- Tokens: {p.input_tokens} in ({p.cache_read_tokens} from cache), "
            f"{p.output_tokens} out; cost {cost}",
            f"- Time: {_minutes(p.run_seconds)} in runs, {_minutes(p.wall_seconds)} first to last",
        ]
    failed = [c for c in cases if c.outcome != "passed"]
    if failed:
        out += ["", "## Tests not passed", ""]
        out += [f"- {c.outcome}: `{c.name}` ({', '.join(c.reqs)})" for c in failed]
    for c in checks:
        if not c.ok and (c.name != SUITE or not cases):
            out += ["", f"### {c.name} output (last {TAIL_LINES} lines)", "", "```"]
            out += [_tail(c.output), "```"]
    return "\n".join(out) + "\n"


def _command(value: str | None, app: Path, target: str) -> list[str] | None:
    return split_command(value) if value else default_command(app, target)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="bench_score.py", description=__doc__.split("\n")[0])
    parser.add_argument("app", type=Path, help="the app folder")
    parser.add_argument("adapter", type=Path, help="the benchmark adapter (.py) for this app")
    parser.add_argument("suite", type=Path, help="the hidden suite folder")
    parser.add_argument("--project", help="the SpoolHQ project that built the app")
    parser.add_argument("--lint", help="lint command (default: just/make lint)")
    parser.add_argument("--test", help="test command (default: just/make test)")
    parser.add_argument("--coverage", help="a command whose output has a coverage TOTAL line")
    parser.add_argument("--out", type=Path, help="write the summary here (default: stdout)")
    args = parser.parse_args(argv)
    app, suite = args.app.resolve(), args.suite.resolve()

    with tempfile.TemporaryDirectory(prefix="bench-score-", ignore_cleanup_errors=True) as tmp:
        copy = Path(tmp) / app.name
        shutil.copytree(app, copy, symlinks=True)
        junit = Path(tmp) / "suite.xml"
        suite_argv, suite_root = suite_command(suite, junit)
        env = {"BENCH_ADAPTER": str(args.adapter.resolve()), "BENCH_APP": str(copy)}
        checks = [run(SUITE, suite_argv, suite_root, env)]
        cases = read_junit(junit) if junit.is_file() else []
        for name, value, target in (("lint", args.lint, "lint"), ("tests", args.test, "test")):
            command = _command(value, copy, target)
            if command:
                checks.append(run(name, command, copy))
        coverage_text = "".join(c.output for c in checks if c.name == "tests")
        if args.coverage:
            checks.append(run("coverage", split_command(args.coverage), copy))
            coverage_text = checks[-1].output
        sizes = file_sizes(copy)
    process = None
    if args.project:
        process = process_numbers(load_settings().projects_dir / args.project)
    summary = render(app.name, cases, checks, coverage_percent(coverage_text), sizes, process)
    if args.out:
        args.out.write_text(summary, encoding="utf-8")
    else:
        sys.stdout.write(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
