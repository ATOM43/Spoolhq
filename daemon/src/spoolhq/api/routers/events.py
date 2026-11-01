"""``/api/projects/{name}/events?since=<seq>``: a project's run-log events, live.

Auth is the first message (``{"type": "auth", "token": …}`` within 5 s; else close
4401), because a browser can't set headers on a WebSocket and a query string ends up in
logs. Browser origins other than ``allowed_origins`` are refused before accept; no
Origin (a non-browser client) is allowed, the token still applies.

Replay without gaps or duplicates: subscribe to the bus first (events queue up), send
the stored events after ``since``, then the queue, skipping what was already sent.

Threading rule: the bus calls the listener on the thread that appended the event (the
run loop's worker, a plan job, a request thread). The listener only hands each event to
the event loop with ``call_soon_threadsafe``; it never awaits, blocks or touches the
socket. Each client has a bounded queue; when it is full the client is dropped with
4408 and reconnects with ``since``, so the run loop never waits on a client.
"""

import asyncio
import contextlib
import hmac
import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from spoolhq.api.schemas.events import AuthMessage, EventEnvelope
from spoolhq.services.projects import project_dir
from spoolhq.services.runs import Event, RunLog, RunRegistry, Subscription

logger = logging.getLogger(__name__)
router = APIRouter()

AUTH_TIMEOUT_S = 5.0
HEARTBEAT_S = 20.0
QUEUE_SIZE = 1000
REPLAY_BATCH = 500
CLOSE_UNAUTHORIZED = 4401
CLOSE_NOT_FOUND = 4404
CLOSE_TOO_SLOW = 4408
CLOSE_GOING_AWAY = 1001


class EventStreams:
    """The open streams, so the daemon can close them all with 1001 on shutdown."""

    def __init__(self) -> None:
        self._stops: set[Callable[[], None]] = set()

    def close_all(self) -> None:
        """Thread-safe; each stream closes itself on its own event loop."""
        for stop in list(self._stops):
            stop()

    def add(self, stop: Callable[[], None]) -> None:
        self._stops.add(stop)

    def discard(self, stop: Callable[[], None]) -> None:
        self._stops.discard(stop)


class _Envelopes:
    """Run log rows → envelopes, caching each run's ticket and attempt numbers."""

    def __init__(self, run_log: RunLog) -> None:
        self._log = run_log
        self._tickets: dict[int, str] = {}
        self._attempts: dict[int, int] = {}

    def __call__(self, event: Event) -> dict[str, Any]:
        if event.run_id not in self._tickets:
            self._tickets[event.run_id] = self._log.get_run(event.run_id).ticket_id
        number = None
        if event.attempt_id is not None:
            if event.attempt_id not in self._attempts:
                self._attempts[event.attempt_id] = self._log.get_attempt(event.attempt_id).number
            number = self._attempts[event.attempt_id]
        envelope = EventEnvelope.of(event, self._tickets[event.run_id], number)
        return envelope.model_dump(mode="json")


async def _authenticate(websocket: WebSocket, token: str) -> bool:
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), AUTH_TIMEOUT_S)
        message = AuthMessage.model_validate_json(raw)
    except (TimeoutError, ValidationError, WebSocketDisconnect, KeyError, RuntimeError):
        return False
    return hmac.compare_digest(message.token.encode(), token.encode())


@router.websocket("/api/projects/{name}/events")
async def events(websocket: WebSocket, name: str, since: int = 0) -> None:
    state = websocket.app.state
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in state.settings.allowed_origins:
        logger.warning(
            "refused an event stream from another origin", extra={"origin": origin[:200]}
        )
        await websocket.close(code=1008)  # before accept: the handshake gets 403
        return
    await websocket.accept()
    if not await _authenticate(websocket, state.token):
        await websocket.close(code=CLOSE_UNAUTHORIZED, reason="unauthorized")
        return
    try:
        folder = project_dir(name, state.settings.projects_dir)
        registry: RunRegistry = state.runs
        runs = registry.open(folder) if (folder / "project.yaml").is_file() else None
    except Exception:  # an invalid name, or a run log that won't open
        runs = None
    if runs is None:
        await websocket.close(code=CLOSE_NOT_FOUND, reason="unknown project")
        return
    await _stream(websocket, state.streams, runs.run_log, runs.bus.subscribe, since)


async def _stream(
    websocket: WebSocket,
    streams: EventStreams,
    run_log: RunLog,
    subscribe: Callable[..., Subscription],
    since: int,
) -> None:
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Event] = asyncio.Queue(QUEUE_SIZE)
    too_slow, stop = asyncio.Event(), asyncio.Event()

    def put(event: Event) -> None:  # on the event loop
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            too_slow.set()

    def listener(subscription: Subscription) -> None:  # on the publishing thread
        while (event := subscription.get(timeout=0)) is not None:
            loop.call_soon_threadsafe(put, event)
        if subscription.lagged:
            loop.call_soon_threadsafe(too_slow.set)

    def request_stop() -> None:
        loop.call_soon_threadsafe(stop.set)

    envelopes = _Envelopes(run_log)
    streams.add(request_stop)
    subscription = subscribe(notify=listener)
    sender = asyncio.create_task(_send(websocket, run_log, envelopes, queue, since))
    closed = asyncio.create_task(_until_disconnect(websocket))
    slow, stopping = asyncio.create_task(too_slow.wait()), asyncio.create_task(stop.wait())
    gone = False
    try:
        await asyncio.wait({sender, closed, slow, stopping}, return_when=asyncio.FIRST_COMPLETED)
        gone = closed.done()
    finally:
        subscription.close()
        streams.discard(request_stop)
        for task in (sender, closed, slow, stopping):
            task.cancel()
        await asyncio.gather(sender, closed, slow, stopping, return_exceptions=True)
    if sender.done() and not sender.cancelled() and sender.exception() is not None:
        logger.warning("event stream failed", extra={"error": type(sender.exception()).__name__})
    code = CLOSE_TOO_SLOW if too_slow.is_set() else CLOSE_GOING_AWAY if stop.is_set() else None
    if code is not None and not gone:
        with contextlib.suppress(Exception):
            await websocket.close(code=code, reason="too_slow" if code == CLOSE_TOO_SLOW else "")


async def _send(
    websocket: WebSocket,
    run_log: RunLog,
    envelopes: _Envelopes,
    queue: "asyncio.Queue[Event]",
    since: int,
) -> None:
    last = since
    while True:  # replay from SQLite
        batch = await asyncio.to_thread(run_log.events_since, last, None, REPLAY_BATCH)
        if not batch:
            break
        for message in await asyncio.to_thread(_convert, envelopes, batch):
            await websocket.send_json(message)
        last = batch[-1].id
    while True:  # then live, skipping what the replay already sent
        try:
            event = await asyncio.wait_for(queue.get(), HEARTBEAT_S)
        except TimeoutError:
            await websocket.send_json({"type": "ping"})
            continue
        if event.id <= last:
            continue
        await websocket.send_json(await asyncio.to_thread(envelopes, event))
        last = event.id


def _convert(envelopes: _Envelopes, batch: list[Event]) -> list[dict[str, Any]]:
    return [envelopes(event) for event in batch]


async def _until_disconnect(websocket: WebSocket) -> None:
    """Returns when the client goes away (clients send nothing after auth)."""
    while (await websocket.receive())["type"] != "websocket.disconnect":
        pass
