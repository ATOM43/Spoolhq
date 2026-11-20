"""The test guard and secret scan through whole runs: a found secret goes back to the
implementer without being printed anywhere, and main's coverage is stored at merges."""

import json
import logging
from pathlib import Path

import pytest

from spoolhq.services.gates import stored_total
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import LocalIntegrator
from spoolhq.services.runs import EventKind, RunRegistry, RunStatus, attempt_dir
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts
from tests.services.runloop.test_notes_files import loop_prompts, outcome, run

# The agent's own transcript and diff hold what it wrote; the gates must add it nowhere.
AGENT_OWN = {EventKind.AGENT_TOOL_CALL, EventKind.AGENT_FILE_EDIT, EventKind.AGENT_MESSAGE}
KEY = "sk-ant-" + "api03-Zx9Yw8Vu7Ts6Rq5Po4Nm3Lk2"


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
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
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
    log = registry.get("demo").run_log
    events = log.events_since(0, limit=100_000)
    printed = [json.dumps(e.payload) for e in events if e.kind not in AGENT_OWN]
    for text in [*printed, json.dumps(first), str(reason), caplog.text, loop_prompts(loop)[1]]:
        assert KEY not in text


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
