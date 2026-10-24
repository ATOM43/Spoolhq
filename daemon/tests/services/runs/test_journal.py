"""The integration journal: rows, states and what counts as open."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from spoolhq.services.runs import (
    IntegrationState,
    RunLog,
    last_integration,
    open_integrations,
    set_integration_state,
    start_integration,
)


@pytest.fixture
def run_log(workspace: Path) -> Iterator[RunLog]:
    with RunLog(workspace, daemon_instance="A") as log:
        yield log


def test_an_integration_moves_through_its_states(run_log: RunLog, workspace: Path) -> None:
    run = run_log.start_run("T04")

    journal = start_integration(run_log, run.id, "T04", "main", "a" * 40)
    assert (journal.state, journal.commit_sha, journal.main_sha) == (
        IntegrationState.MERGING,
        None,
        "a" * 40,
    )
    committed = set_integration_state(
        run_log, journal.id, IntegrationState.COMMITTED, commit_sha="b" * 40
    )
    assert committed.commit_sha == "b" * 40
    advanced = set_integration_state(run_log, journal.id, IntegrationState.ADVANCED)
    assert (advanced.state, advanced.commit_sha) == (IntegrationState.ADVANCED, "b" * 40)
    assert open_integrations(run_log) == [advanced]

    set_integration_state(run_log, journal.id, IntegrationState.DONE)
    assert open_integrations(run_log) == []
    # Committed: another connection (a restarted daemon) sees the same row.
    with RunLog(workspace, daemon_instance="B") as other:
        assert open_integrations(other) == []


def test_abandoned_is_not_open(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    first = start_integration(run_log, run.id, "T04", "main", "a" * 40)
    second = start_integration(run_log, run.id, "T04", "main", "c" * 40)

    set_integration_state(run_log, first.id, IntegrationState.ABANDONED)

    assert [row.id for row in open_integrations(run_log)] == [second.id]


def test_last_integration_is_the_latest_done(run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    assert last_integration(run_log) is None
    first = start_integration(run_log, run.id, "T04", "main", "a" * 40)
    set_integration_state(run_log, first.id, IntegrationState.COMMITTED, commit_sha="b" * 40)
    assert last_integration(run_log) is None

    set_integration_state(run_log, first.id, IntegrationState.DONE)
    second = start_integration(run_log, run.id, "T05", "main", "b" * 40)
    set_integration_state(run_log, second.id, IntegrationState.ABANDONED)
    last = last_integration(run_log)
    assert last is not None
    assert (last.id, last.ticket_id, last.commit_sha) == (first.id, "T04", "b" * 40)

    third = start_integration(run_log, run.id, "T06", "main", "b" * 40)
    set_integration_state(run_log, third.id, IntegrationState.DONE, commit_sha="c" * 40)
    last = last_integration(run_log)
    assert last is not None
    assert (last.ticket_id, last.commit_sha) == ("T06", "c" * 40)


def test_unknown_integration(run_log: RunLog) -> None:
    with pytest.raises(KeyError, match="integration 99 not found"):
        set_integration_state(run_log, 99, IntegrationState.DONE)
