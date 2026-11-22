"""The test guard and secret scan through whole runs: a found secret goes back to the
implementer and is stored nowhere, and main's coverage is stored at merges."""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from spoolhq.services.gates import GateRun, GateStatus, store_total, stored_total
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import LocalIntegrator
from spoolhq.services.runloop.model import RunContext
from spoolhq.services.runloop.quality import _coverage
from spoolhq.services.runs import RunRegistry, RunStatus, attempt_dir, state_db_path
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts, gate_result
from tests.services.runloop.test_notes_files import loop_prompts, outcome, run

KEY = "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"
RANDOM = "q8Zr2Lx0Vb7Nw4Kp1Ts9Hd3Fy6Jm5Gc0Ua"


def stored_texts(registry: RunRegistry, project: Path) -> list[str]:
    """Every event payload, every file under the workspace's runs and state folders (the
    database and its WAL as bytes) and the run reasons."""
    log = registry.get("demo").run_log
    texts = [json.dumps(e.payload, ensure_ascii=False) for e in log.events_since(0, limit=100_000)]
    texts += [str(run.reason) for run in log.list_runs()]
    folders = [project / "runs", state_db_path(project).parent]
    for path in (p for folder in folders for p in folder.rglob("*") if p.is_file()):
        texts.append(path.read_bytes().decode("utf-8", errors="replace"))
    return texts


def gates_json(registry: RunRegistry, index: int = 0, run_index: int = 0) -> dict[str, object]:
    log = registry.get("demo").run_log
    attempt = log.list_attempts(log.list_runs()[run_index].id)[index]
    text = (attempt_dir(attempt.workspace, attempt) / "gates.json").read_text("utf-8")
    return dict(json.loads(text))


@pytest.mark.integration
def test_a_secret_goes_back_without_being_printed(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    project: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    received = registry.get("demo").bus.subscribe(maxsize=100_000)
    leaky = transcripts.implement({"config.py": f'API = "{KEY}"\n'})
    fixed = transcripts.implement({"config.py": 'import os\nAPI = os.environ["API"]\n'})
    loop, _ = make_loop(
        [leaky, fixed],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )
    run(loop)
    status, reason, attempts = outcome(registry)
    assert (status, attempts) == (
        RunStatus.DONE,
        [("initial", "gates_failed"), ("gate_retry", "approved")],
    )
    first = gates_json(registry)
    results = {r["name"]: r for r in first["results"]}  # type: ignore[attr-defined]
    message = "Possible secret in config.py:1 (Anthropic key)"
    assert results["secret_scan"]["status"] == "failed"
    assert results["secret_scan"]["excerpt"] == message
    note = "Coverage not compared: no gates.coverage_report in project.yaml"
    assert results["test_guard"]["excerpt"] == note
    assert message in loop_prompts(loop)[1]
    # The reviewer only ever saw the fixed attempt.
    assert len(loop.agents.reviewer.calls) == 1  # type: ignore[attr-defined]
    streamed = []
    while (event := received.get(timeout=0)) is not None:
        streamed.append(json.dumps(event.payload))
    assert streamed
    texts = [*stored_texts(registry, project), *streamed, caplog.text, loop_prompts(loop)[1]]
    assert all(KEY not in text for text in texts)
    assert any("[redacted: Anthropic key]" in text for text in texts)


@pytest.mark.integration
def test_a_high_entropy_value_is_redacted_after_the_scan_finds_it(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    project: Path,
) -> None:
    leaky = transcripts.implement({"config.py": f'blob = "{RANDOM}"\n'})
    fixed = transcripts.implement({"config.py": "blob = None\n"})
    loop, _ = make_loop(
        [leaky, fixed],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )
    run(loop)
    status, _, attempts = outcome(registry)
    assert (status, attempts[0]) == (RunStatus.DONE, ("initial", "gates_failed"))
    texts = stored_texts(registry, project)
    assert all(RANDOM not in text for text in texts)
    log = registry.get("demo").run_log
    first = log.list_attempts(log.list_runs()[0].id)[0]
    diff = (attempt_dir(first.workspace, first) / "diff.patch").read_text("utf-8")
    assert '+blob = "[redacted: high-entropy string]"' in diff


def set_coverage_report(projects_dir: Path) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    settings.gates.coverage_report = "coverage.xml"
    save_project(settings, projects_dir=projects_dir)


def report(rate: str) -> dict[str, str]:
    return {"coverage.xml": f'<?xml version="1.0" ?>\n<coverage line-rate="{rate}">\n'}


@pytest.mark.integration
def test_the_first_merge_stores_coverage_and_a_drop_goes_back(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    projects_dir: Path,
    project: Path,
) -> None:
    set_coverage_report(projects_dir)
    first, _ = make_loop(
        [transcripts.implement(report("0.912"))],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )
    run(first)
    guard = {r["name"]: r for r in gates_json(registry)["results"]}["test_guard"]  # type: ignore[attr-defined]
    assert guard["excerpt"] == "Coverage 91.2% recorded; main has none stored yet"
    assert stored_total(project) == 91.2

    dropped = transcripts.implement(report("0.884"))
    kept = transcripts.implement(report("0.909"))
    second, _ = make_loop(
        [dropped, kept],
        [transcripts.review("approve")],
        integrator=LocalIntegrator(clock=clock),
    )
    run(second)
    assert "Coverage fell from 91.2% to 88.4%" in loop_prompts(second)[1]
    log = registry.get("demo").run_log
    latest = log.list_runs()[0]
    assert latest.status is RunStatus.DONE
    assert stored_total(project) == 90.9


def coverage_ctx(worktree: Path, workspace: Path, report: str | None) -> RunContext:
    gates = SimpleNamespace(coverage_report=report)
    ctx = SimpleNamespace(
        project=SimpleNamespace(gates=gates),
        worktree=SimpleNamespace(path=worktree),
        workspace=workspace,
    )
    return cast(RunContext, ctx)


PASSED_TEST = GateRun((gate_result("test", GateStatus.PASSED),))
MISSING = "Coverage report coverage.xml wasn't written; the test command must write it"


@pytest.mark.parametrize("content", [None, "not a report", '{"totals": {}}'])
def test_a_missing_or_unreadable_report_fails_once_main_has_a_total(
    tmp_path: Path, content: str | None
) -> None:
    if content is not None:
        (tmp_path / "coverage.xml").write_text(content, encoding="utf-8")
    store_total(tmp_path, 91.2, "T01")
    coverage = _coverage(coverage_ctx(tmp_path, tmp_path, "coverage.xml"), PASSED_TEST)
    assert (coverage.problem, coverage.stored, coverage.total) == (MISSING, 91.2, None)


def test_a_missing_report_skips_while_main_has_no_total(tmp_path: Path) -> None:
    coverage = _coverage(coverage_ctx(tmp_path, tmp_path, "coverage.xml"), PASSED_TEST)
    assert coverage.problem == ""
    assert coverage.note == "Coverage not compared: coverage.xml is missing or unreadable"


def test_no_coverage_report_changes_nothing(tmp_path: Path) -> None:
    store_total(tmp_path, 91.2, "T01")
    coverage = _coverage(coverage_ctx(tmp_path, tmp_path, None), PASSED_TEST)
    assert coverage.problem == ""
    assert coverage.note == "Coverage not compared: no gates.coverage_report in project.yaml"
