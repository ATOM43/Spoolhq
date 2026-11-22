"""The built-in gates the run loop adds after the command gates (file size, test guard,
secret scan), and main's coverage total kept at each merge. See ``docs/gates.md``."""

import json

from spoolhq.services.gates import (
    Coverage,
    GateResult,
    GateRun,
    GateStatus,
    check_file_sizes,
    check_tests,
    high_entropy_values,
    read_total,
    scan_secrets,
    store_total,
    stored_total,
)
from spoolhq.services.runloop.guards import ticket_changes
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runs import ArtifactName, RunLog, attempt_files


def _coverage(ctx: RunContext, commands: GateRun) -> Coverage:
    report = ctx.project.gates.coverage_report
    if report is None:
        return Coverage(note="Coverage not compared: no gates.coverage_report in project.yaml")
    test = next((r for r in commands.results if r.name == "test"), None)
    if test is None or test.status is not GateStatus.PASSED:
        return Coverage(note="Coverage not compared: the test gate didn't pass")
    total = read_total(ctx.worktree.path, report)
    stored = stored_total(ctx.workspace)
    if total is None and stored is not None:
        problem = f"Coverage report {report} wasn't written; the test command must write it"
        return Coverage(stored=stored, problem=problem)
    if total is None:
        return Coverage(note=f"Coverage not compared: {report} is missing or unreadable")
    if stored is None:
        return Coverage(total, None, f"Coverage {total:.1f}% recorded; main has none stored yet")
    return Coverage(total, stored)


def builtin_gates(
    ctx: RunContext, commands: GateRun
) -> tuple[tuple[GateResult, ...], float | None, set[str]]:
    """The built-in gates' results on the ticket's diff, its coverage total, and the
    high-entropy values the secret scan found (to redact from the attempt's records)."""
    settings = ctx.project.gates
    changes = ticket_changes(ctx)
    sizes = check_file_sizes(
        ctx.worktree.path,
        [(change.path, change.before) for change in changes if not change.deleted],
        settings.max_file_lines,
        settings.max_file_lines_exempt,
    )
    coverage = _coverage(ctx, commands)
    done_when = [item.text for item in ctx.ticket.done_when]
    guard = check_tests(ctx.worktree.path, changes, settings.test_paths, done_when, coverage)
    secrets = scan_secrets(changes, settings.secret_scan_allow)
    found = set()
    if secrets.status is GateStatus.FAILED:
        found = high_entropy_values(changes, settings.secret_scan_allow)
    return (sizes, guard, secrets), coverage.total, found


def record_main_coverage(run_log: RunLog, run_id: int, ticket_id: str) -> None:
    """At a merge: the coverage total of the gates that landed becomes main's."""
    attempts = run_log.list_attempts(run_id)
    if not attempts:
        return
    attempt = attempts[-1]
    path = attempt_files(attempt.workspace, attempt).get(ArtifactName.GATES.value)
    if path is None:
        return
    try:
        total = json.loads(path.read_text(encoding="utf-8")).get("coverage")
    except (OSError, ValueError, AttributeError):
        return
    if isinstance(total, int | float) and not isinstance(total, bool):
        store_total(attempt.workspace, float(total), ticket_id)
