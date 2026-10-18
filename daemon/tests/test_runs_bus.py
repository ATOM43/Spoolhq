"""The event bus: order, filtering, lag and resync, and isolation of subscribers."""

import threading
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import FixedClock

from spoolhq.services.runs import Event, EventBus, EventKind, RunLog, Subscription


@pytest.fixture
def bus() -> EventBus:
    return EventBus()


@pytest.fixture
def run_log(workspace: Path, clock: FixedClock, bus: EventBus) -> Iterator[RunLog]:
    with RunLog(workspace, bus=bus, clock=clock, daemon_instance="A") as log:
        yield log


def drain(sub: Subscription) -> list[Event]:
    events = []
    while (event := sub.get(timeout=0)) is not None:
        events.append(event)
    return events


def test_subscriber_receives_events_in_id_order(bus: EventBus, run_log: RunLog) -> None:
    with bus.subscribe() as sub:
        run = run_log.start_run("T04")
        for i in range(5):
            run_log.append_event(run.id, EventKind.LOG, {"i": i})
        received = drain(sub)
    assert received == run_log.events_since(0)
    assert sub.last_id == received[-1].id


def test_run_filter_excludes_other_runs(bus: EventBus, run_log: RunLog) -> None:
    a = run_log.start_run("T04")
    b = run_log.start_run("T05")
    with bus.subscribe(run_id=b.id) as sub:
        run_log.append_event(a.id, EventKind.LOG, {"run": "a"})
        run_log.append_event(b.id, EventKind.LOG, {"run": "b"})
        run_log.append_event(a.id, EventKind.LOG, {"run": "a"})
        received = drain(sub)
    assert [e.payload for e in received] == [{"run": "b"}]


def test_full_subscriber_lags_and_resyncs_from_the_log(bus: EventBus, run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    with bus.subscribe(maxsize=2) as sub:
        for i in range(5):
            run_log.append_event(run.id, EventKind.LOG, {"i": i})
        assert sub.lagged
        received = drain(sub)
        assert [e.payload["i"] for e in received] == [0, 1]
        assert sub.get(timeout=5) is None  # lagged and empty: returns at once

        missing = run_log.events_since(sub.last_id)
        assert [e.payload["i"] for e in missing] == [2, 3, 4]
    assert bus.subscriber_count == 0

    with bus.subscribe(maxsize=2) as again:
        run_log.append_event(run.id, EventKind.LOG, {"i": 5})
        assert [e.payload["i"] for e in drain(again)] == [5]
        assert not again.lagged


def test_last_id_before_any_get_marks_the_subscription_start(
    bus: EventBus, run_log: RunLog
) -> None:
    run = run_log.start_run("T04")
    run_log.append_event(run.id, EventKind.LOG, {"before": True})
    with bus.subscribe(maxsize=1) as sub:
        start = sub.last_id
        assert start == run_log.events_since(0)[-1].id
        for i in range(3):
            run_log.append_event(run.id, EventKind.LOG, {"i": i})
        assert sub.lagged
        assert [e.payload["i"] for e in run_log.events_since(start)] == [0, 1, 2]


def test_publish_completes_while_a_subscriber_never_reads(bus: EventBus, run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    with bus.subscribe(maxsize=3) as stuck, bus.subscribe(maxsize=100) as reader:
        finished = threading.Event()

        def publish_many() -> None:
            for i in range(50):
                run_log.append_event(run.id, EventKind.LOG, {"i": i})
            finished.set()

        thread = threading.Thread(target=publish_many)
        thread.start()
        assert finished.wait(timeout=30)
        thread.join()
        assert stuck.lagged
        assert len(drain(stuck)) == 3
        assert len(drain(reader)) == 50


def test_a_failing_subscriber_does_not_affect_the_others(
    bus: EventBus, run_log: RunLog, monkeypatch: pytest.MonkeyPatch
) -> None:
    run = run_log.start_run("T04")
    with bus.subscribe() as broken, bus.subscribe() as healthy:

        def explode(event: Event) -> bool:
            raise RuntimeError("queue broke")

        monkeypatch.setattr(broken, "_offer", explode)
        for i in range(3):
            run_log.append_event(run.id, EventKind.LOG, {"i": i})
        assert broken.lagged
        assert [e.payload["i"] for e in drain(healthy)] == [0, 1, 2]


def test_a_failing_notify_callback_does_not_affect_the_others(
    bus: EventBus, run_log: RunLog
) -> None:
    run = run_log.start_run("T04")
    calls: list[int] = []

    def boom(sub: Subscription) -> None:
        raise RuntimeError("callback broke")

    with (
        bus.subscribe(notify=boom) as broken,
        bus.subscribe(notify=lambda sub: calls.append(sub.maxsize)) as healthy,
    ):
        event = run_log.append_event(run.id, EventKind.LOG, {})
        assert broken.lagged
        assert broken.get(timeout=0) == event  # queued before the callback failed
        assert drain(healthy) == [event]
        assert calls == [1000]


def test_get_waits_for_an_event_and_times_out(bus: EventBus, run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    with bus.subscribe() as sub:
        assert sub.get(timeout=0.05) is None

        timer = threading.Timer(0.05, run_log.append_event, (run.id, EventKind.LOG, {"x": 1}))
        timer.start()
        event = sub.get(timeout=10)
        timer.join()
        assert event is not None
        assert event.payload == {"x": 1}


def test_close_wakes_a_waiting_get(bus: EventBus) -> None:
    sub = bus.subscribe()
    results: list[Event | None] = []
    thread = threading.Thread(target=lambda: results.append(sub.get()))
    thread.start()
    time.sleep(0.05)
    sub.close()
    thread.join(timeout=10)
    assert results == [None]
    assert sub.closed
    sub.close()
    assert bus.subscriber_count == 0


def test_closed_subscription_receives_nothing(bus: EventBus, run_log: RunLog) -> None:
    run = run_log.start_run("T04")
    sub = bus.subscribe()
    sub.close()
    run_log.append_event(run.id, EventKind.LOG, {})
    assert sub.get(timeout=0) is None


def test_maxsize_must_be_positive(bus: EventBus) -> None:
    with pytest.raises(ValueError, match="maxsize"):
        bus.subscribe(maxsize=0)
