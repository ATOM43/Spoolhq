"""services/runs/totals.py: a workspace's usage, latest activity and a run's step."""

from pathlib import Path

from spoolhq.services.runs import AttemptKind, EventKind, RunLog, latest_phase, project_totals


def test_an_empty_log_has_no_usage_and_no_activity(tmp_path: Path) -> None:
    with RunLog(tmp_path, daemon_instance="A") as log:
        totals = project_totals(log)
    assert (totals.tokens, totals.cost_micro_usd, totals.last_activity) == (0, None, None)


def test_usage_sums_tokens_and_cost_across_runs(tmp_path: Path) -> None:
    with RunLog(tmp_path, daemon_instance="A") as log:
        first = log.start_attempt(log.start_run("T01").id, AttemptKind.INITIAL)
        log.record_usage(first.id, 100, 50)  # a subscription: tokens, no cost
        second = log.start_attempt(log.start_run("T02").id, AttemptKind.INITIAL)
        log.record_usage(second.id, 1000, 500, 840_000)  # an API key: priced
        third = log.start_attempt(log.start_run("T03").id, AttemptKind.INITIAL)
        log.record_usage(third.id, 30, 20)
        totals = project_totals(log)
    assert totals.tokens == 200  # priced attempts count as dollars, not twice
    assert totals.cost_micro_usd == 840_000


def test_last_activity_is_the_latest_event_and_the_step_its_phase(tmp_path: Path) -> None:
    with RunLog(tmp_path, daemon_instance="A") as log:
        run = log.start_run("T01")
        assert latest_phase(log, run.id) is None
        log.append_event(run.id, EventKind.RUN_PHASE, {"phase": "implement", "text": "x"})
        log.append_event(run.id, EventKind.RUN_PHASE, {"phase": "gates", "text": "y"})
        latest = log.events_since(0)[-1]
        assert project_totals(log).last_activity == latest.ts
        assert latest_phase(log, run.id) == "gates"
