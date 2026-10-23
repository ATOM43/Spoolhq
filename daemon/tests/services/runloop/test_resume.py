"""ResumeTimer: fires at reset_at + 60 s by the injected clock, and stops on close."""

import threading
from datetime import timedelta

from spoolhq.services.runloop import RESUME_DELAY, ResumeTimer
from tests.services.runloop.conftest import RESET_AT, ManualClock


def test_fires_once_at_reset_plus_a_minute(clock: ManualClock) -> None:
    fired: list[str] = []
    timer = ResumeTimer(clock, fired.append, poll_s=3600)
    try:
        assert timer.schedule("demo", RESET_AT) == RESET_AT + RESUME_DELAY
        clock.now = RESET_AT + timedelta(seconds=59)
        assert timer.check() == []
        clock.now = RESET_AT + timedelta(seconds=60)
        assert timer.check() == ["demo"]
        assert timer.check() == []
        assert fired == ["demo"]
    finally:
        timer.close()


def test_cancel_and_close_drop_the_schedule(clock: ManualClock) -> None:
    timer = ResumeTimer(clock, lambda _project: None, poll_s=3600)
    timer.schedule("demo", RESET_AT)
    timer.cancel("demo")
    assert timer.due_at("demo") is None
    timer.schedule("other", RESET_AT)
    timer.close()
    assert timer.due_at("other") is None


def test_the_polling_thread_fires_and_a_failing_callback_is_logged(clock: ManualClock) -> None:
    done = threading.Event()

    def on_due(project: str) -> None:
        done.set()
        raise RuntimeError("resume failed")

    timer = ResumeTimer(clock, on_due, poll_s=0.01)
    try:
        clock.now = RESET_AT + RESUME_DELAY
        timer.schedule("demo", RESET_AT)
        assert done.wait(5)
    finally:
        timer.close()
