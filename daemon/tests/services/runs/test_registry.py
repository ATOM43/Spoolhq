"""services/runs: the registry that opens each workspace's run log and event bus."""

from pathlib import Path

from spoolhq.services.runs import RunLog, RunRegistry, RunStatus


def test_bus_starts_at_the_databases_last_event(workspace: Path, projects_dir: Path) -> None:
    with RunLog(workspace, daemon_instance="previous") as log:
        run = log.start_run("T04")
        log.set_run_status(run.id, RunStatus.PAUSED)
        log.set_run_status(run.id, RunStatus.DONE)
        log.set_run_status(log.start_run("T05").id, RunStatus.DONE)
        existing = log.events_since(0)
    assert [event.id for event in existing] == [1, 2, 3, 4, 5]

    registry = RunRegistry.start(projects_dir, daemon_instance="now")
    try:
        runs = registry.get("demo")
        subscription = runs.bus.subscribe(maxsize=1)
        # Lags before it receives anything: it must resync from 5, not replay from 0.
        new_run = runs.run_log.start_run("T06")
        runs.run_log.set_run_status(new_run.id, RunStatus.DONE)
        assert subscription.lagged
        assert subscription.last_id == 5
        assert [event.id for event in runs.run_log.events_since(subscription.last_id)] == [
            6,
            7,
        ]
    finally:
        registry.close()


def test_bus_of_an_empty_database_starts_at_zero(workspace: Path, projects_dir: Path) -> None:
    registry = RunRegistry.start(projects_dir, daemon_instance="now")
    try:
        assert registry.get("demo").bus.subscribe().last_id == 0
    finally:
        registry.close()
