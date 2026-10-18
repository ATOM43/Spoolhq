"""In-process fan-out of run-log events: one ``EventBus`` per workspace.

The bus is synchronous and thread-safe and never touches the database. ``publish``
never blocks: each subscriber has a bounded queue, and a subscriber whose queue is full
is marked ``lagged`` and receives nothing more. It keeps what was already queued; the
consumer then catches up with ``RunLog.events_since(sub.last_id)`` and subscribes
again. ``docs/runs.md`` describes the contract.
"""

import logging
import threading
from collections import deque
from collections.abc import Callable
from types import TracebackType
from typing import Self

from spoolhq.services.runs.model import Event

logger = logging.getLogger(__name__)

DEFAULT_MAXSIZE = 1000

Notify = Callable[["Subscription"], None]


class Subscription:
    """A consumer's queue of events, optionally only those of one run.

    ``last_id`` is the id of the last event ``get`` returned; before the first one, the
    id of the last event the bus had published when the subscription started. Every
    event after it is either still queued or, once ``lagged``, readable with
    ``RunLog.events_since(last_id)``.
    """

    def __init__(
        self,
        bus: "EventBus",
        *,
        run_id: int | None,
        maxsize: int,
        last_id: int,
        notify: Notify | None,
    ) -> None:
        self.run_id = run_id
        self.maxsize = maxsize
        self._bus = bus
        self._notify = notify
        self._items: deque[Event] = deque()
        self._cond = threading.Condition()
        self._last_id = last_id
        self._lagged = False
        self._closed = False

    @property
    def last_id(self) -> int:
        with self._cond:
            return self._last_id

    @property
    def lagged(self) -> bool:
        with self._cond:
            return self._lagged

    @property
    def closed(self) -> bool:
        with self._cond:
            return self._closed

    def get(self, timeout: float | None = None) -> Event | None:
        """The next queued event, waiting up to ``timeout`` seconds (forever if None).

        Returns None on timeout, and at once when nothing is queued and the
        subscription is lagged or closed (no more events will arrive).
        """
        with self._cond:
            ready = self._cond.wait_for(
                lambda: bool(self._items) or self._lagged or self._closed, timeout
            )
            if not ready or not self._items:
                return None
            event = self._items.popleft()
            self._last_id = event.id
            return event

    def close(self) -> None:
        """Stop receiving events and wake a waiting ``get``. Safe to call twice."""
        self._bus._remove(self)
        with self._cond:
            self._closed = True
            self._cond.notify_all()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _wants(self, event: Event) -> bool:
        return self.run_id is None or event.run_id == self.run_id

    def _offer(self, event: Event) -> bool:
        """Queue ``event``; returns False (and marks the subscription lagged) if full."""
        with self._cond:
            if self._closed or self._lagged:
                return False
            if len(self._items) >= self.maxsize:
                self._lagged = True
                self._cond.notify_all()
                return False
            self._items.append(event)
            self._cond.notify_all()
            return True

    def _mark_lagged(self) -> None:
        with self._cond:
            self._lagged = True
            self._cond.notify_all()

    def _call_notify(self) -> None:
        if self._notify is not None:
            self._notify(self)


class EventBus:
    """Fan events out to subscribers. ``publish`` never blocks and never raises."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[Subscription] = []
        self._last_id = 0

    def start_at(self, last_id: int) -> None:
        """Treat ``last_id`` as already published, so new subscribers resync after it.

        Called with the database's highest event id when a run log is opened; without
        it, a subscriber that lags at once would replay every older run's events.
        """
        with self._lock:
            self._last_id = max(self._last_id, last_id)

    def subscribe(
        self,
        run_id: int | None = None,
        maxsize: int = DEFAULT_MAXSIZE,
        *,
        notify: Notify | None = None,
    ) -> Subscription:
        """Receive every event published from now on (only ``run_id``'s if given).

        ``notify`` is called with the subscription after an event is queued or the
        subscription becomes lagged, on the publishing thread. It must return quickly
        and must not call the bus or the run log (to wake an asyncio loop, use
        ``loop.call_soon_threadsafe``); an exception from it is logged and ignored.
        """
        if maxsize < 1:
            raise ValueError(f"maxsize must be at least 1, got {maxsize}")
        with self._lock:
            subscription = Subscription(
                self, run_id=run_id, maxsize=maxsize, last_id=self._last_id, notify=notify
            )
            self._subscribers.append(subscription)
        return subscription

    def publish(self, event: Event) -> None:
        """Queue ``event`` for every interested subscriber; never blocks or raises."""
        with self._lock:
            self._last_id = max(self._last_id, event.id)
            subscribers = list(self._subscribers)
            for subscription in subscribers:
                self._deliver(subscription, event)

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def _deliver(self, subscription: Subscription, event: Event) -> None:
        try:
            if not subscription._wants(event):
                return
            if not subscription._offer(event):
                # Full: it is lagged now and gets nothing more.
                self._subscribers.remove(subscription)
            subscription._call_notify()
        except Exception:
            logger.exception(
                "event subscriber failed; it is marked lagged",
                extra={"event_id": event.id, "run_id": event.run_id},
            )
            try:
                subscription._mark_lagged()
                if subscription in self._subscribers:
                    self._subscribers.remove(subscription)
            except Exception:
                logger.exception("could not mark a failed event subscriber lagged")

    def _remove(self, subscription: Subscription) -> None:
        with self._lock:
            if subscription in self._subscribers:
                self._subscribers.remove(subscription)
