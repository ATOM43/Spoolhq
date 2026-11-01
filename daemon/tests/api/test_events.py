"""The event WebSocket: auth, origin, a whole fake run in order, replay without gaps or
duplicates, a slow client that never slows the run, and shutdown."""

import asyncio
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from starlette.testclient import WebSocketTestSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from spoolhq.api.routers import events
from spoolhq.services.runs import EventKind, RunLog
from tests.api.test_runs import auth, follow

URL = "/api/projects/demo/events"


def ws_url(client: TestClient, path: str = URL) -> str:
    """TestClient defaults to ws://testserver, which the Host check refuses."""
    return f"ws://{client.base_url.netloc.decode()}{path}"


@contextmanager
def connect(
    client: TestClient, token: str, since: int = 0, **kwargs: Any
) -> Iterator[WebSocketTestSession]:
    """An authenticated stream, once the server has subscribed to the bus."""
    with client.websocket_connect(ws_url(client, f"{URL}?since={since}"), **kwargs) as ws:
        bus = client.app.state.runs.open(client.app.state.settings.projects_dir / "demo").bus  # type: ignore[attr-defined]
        before = bus.subscriber_count
        ws.send_json({"type": "auth", "token": token})
        for _ in range(200):
            if bus.subscriber_count > before:
                break
            time.sleep(0.01)
        yield ws
        # TestClient cancels the app right after its own close; let the handler end
        # first, as it does on a real server, or the cancel races it on a slow machine.
        ws.close()
        wait_closed(client)


def wait_closed(client: TestClient) -> None:
    streams = client.app.state.streams  # type: ignore[attr-defined]
    for _ in range(500):
        if streams.count == 0:
            return
        time.sleep(0.01)
    raise AssertionError("the event stream did not end")


def receive(ws: WebSocketTestSession, count: int) -> list[dict[str, Any]]:
    messages = []
    while len(messages) < count:
        message = ws.receive_json()
        if message.get("type") != "ping":
            messages.append(message)
    return messages


def close_code(ws: WebSocketTestSession) -> int:
    message = ws.receive()
    assert message["type"] == "websocket.close", message
    return int(message["code"])


def run_log(client: TestClient, workspace: Path) -> RunLog:
    return client.app.state.runs.open(workspace).run_log  # type: ignore[attr-defined,no-any-return]


def emit(log: RunLog, run_id: int, count: int, pause_s: float = 0.0) -> threading.Thread:
    """Append ``count`` log events from another thread, like the run loop's worker."""

    def work() -> None:
        for index in range(count):
            log.append_event(run_id, EventKind.LOG, {"message": f"line {index}"})
            if pause_s:
                time.sleep(pause_s)

    thread = threading.Thread(target=work)
    thread.start()
    return thread


# --- auth and origin ---------------------------------------------------------------------


def test_wrong_or_missing_token_closes_4401(
    client: TestClient, token: str, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    with client.websocket_connect(ws_url(client)) as ws:
        ws.send_json({"type": "auth", "token": "wrong"})
        assert close_code(ws) == 4401
    with client.websocket_connect(ws_url(client)) as ws:
        ws.send_text("not json")
        assert close_code(ws) == 4401
    monkeypatch.setattr(events, "AUTH_TIMEOUT_S", 0.2)
    with client.websocket_connect(ws_url(client)) as ws:
        assert close_code(ws) == 4401  # nothing sent within the timeout


def test_origin_is_checked_before_accept(client: TestClient, token: str, workspace: Path) -> None:
    with pytest.raises(WebSocketDisconnect) as refused:
        client.websocket_connect(
            ws_url(client), headers={"Origin": "https://evil.example"}
        ).__enter__()
    assert refused.value.code == 1008
    with connect(client, token, headers={"Origin": "tauri://localhost"}) as ws:
        client.app.state.streams.close_all()  # type: ignore[attr-defined]
        assert close_code(ws) == 1001  # what the daemon sends on shutdown


def test_unknown_project_closes_4404(client: TestClient, token: str) -> None:
    with client.websocket_connect(ws_url(client, "/api/projects/nope/events")) as ws:
        ws.send_json({"type": "auth", "token": token})
        assert close_code(ws) == 4404


# --- a whole run, replay -----------------------------------------------------------------


@pytest.mark.integration
def test_a_client_receives_every_event_of_a_fake_run_in_order(
    run_client: TestClient, token: str, run_project: Path
) -> None:
    run_log(run_client, run_project)
    with connect(run_client, token) as ws:
        run_client.post("/api/projects/demo/run/next", headers=auth(token))
        run = follow(run_client, token)["run"]
        assert run["status"] == "done"
        stored = run_log(run_client, run_project).events_since(0, run_id=run["id"], limit=10_000)
        received = receive(ws, len(stored))
    seqs = [message["seq"] for message in received]
    assert seqs == sorted(set(seqs))
    assert seqs == [event.id for event in stored]
    assert [m["type"] for m in received] == [event.kind.value for event in stored]
    assert {m["ticket"] for m in received} == {"T07"}
    started = next(m for m in received if m["type"] == "attempt.started")
    assert started["attempt"] == started["data"]["number"] == 1

    middle = stored[len(stored) // 2].id
    with connect(run_client, token, since=middle) as replay:
        rest = receive(replay, len([e for e in stored if e.id > middle]))
    assert [m["seq"] for m in rest] == [e.id for e in stored if e.id > middle]


def test_no_gap_or_duplicate_at_the_replay_seam(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = run_log(client, workspace)
    run = log.start_run("T01")
    thread = emit(log, run.id, 300, pause_s=0.001)
    time.sleep(0.05)  # some events stored before the client connects, more after
    with connect(client, token, since=0) as ws:
        thread.join()
        expected = [event.id for event in log.events_since(0, limit=10_000)]
        assert [m["seq"] for m in receive(ws, len(expected))] == expected


# --- a slow client -----------------------------------------------------------------------


def _timed_emit(log: RunLog, run_id: int) -> float:
    start = time.monotonic()
    emit(log, run_id, 200).join()
    return time.monotonic() - start


def test_subscribing_from_latest_seq_skips_history_but_not_later_events(
    client: TestClient, token: str, workspace: Path
) -> None:
    log = run_log(client, workspace)
    run = log.start_run("T01")
    emit(log, run.id, 3).join()  # history the client already has through REST
    project = client.get("/api/projects/demo", headers=auth(token)).json()
    current = client.get("/api/projects/demo/runs/current", headers=auth(token)).json()
    assert project["latest_seq"] == current["latest_seq"] == log.last_event_id() > 0
    log.append_event(run.id, EventKind.LOG, {"message": "between REST and subscribe"})
    with connect(client, token, since=project["latest_seq"]) as ws:
        log.append_event(run.id, EventKind.LOG, {"message": "live"})
        messages = receive(ws, 2)
    assert [m["data"]["message"] for m in messages] == ["between REST and subscribe", "live"]
    assert messages[0]["seq"] == project["latest_seq"] + 1


def test_a_client_that_never_reads_is_dropped_and_never_slows_the_run(
    client: TestClient, token: str, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log = run_log(client, workspace)
    run = log.start_run("T01")
    alone = _timed_emit(log, run.id)

    async def stuck(_self: WebSocket, _data: Any, mode: str = "text") -> None:
        await asyncio.Event().wait()  # like a socket whose buffer never drains

    monkeypatch.setattr(events, "QUEUE_SIZE", 10)
    monkeypatch.setattr(WebSocket, "send_json", stuck)
    with connect(client, token, since=log.last_event_id()) as ws:
        with_client = _timed_emit(log, run.id)
        assert close_code(ws) == 4408
    assert with_client < alone * 5 + 1.0
    assert client.app.state.runs.open(workspace).bus.subscriber_count == 0  # type: ignore[attr-defined]


@pytest.mark.integration
def test_a_stuck_client_during_a_fake_run(
    run_client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def stuck(_self: WebSocket, _data: Any, mode: str = "text") -> None:
        await asyncio.Event().wait()

    monkeypatch.setattr(events, "QUEUE_SIZE", 10)
    monkeypatch.setattr(WebSocket, "send_json", stuck)
    with connect(run_client, token) as ws:
        run_client.post("/api/projects/demo/run/next", headers=auth(token))
        assert follow(run_client, token)["run"]["status"] == "done"
        assert close_code(ws) == 4408


def test_heartbeat_and_cleanup(
    client: TestClient, token: str, workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(events, "HEARTBEAT_S", 0.05)
    bus = client.app.state.runs.open(workspace).bus  # type: ignore[attr-defined]
    with connect(client, token) as ws:
        assert ws.receive_json() == {"type": "ping"}
    for _ in range(100):
        if bus.subscriber_count == 0:
            break
        time.sleep(0.01)
    assert bus.subscriber_count == 0
