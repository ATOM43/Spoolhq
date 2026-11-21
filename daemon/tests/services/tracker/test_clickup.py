"""The ClickUp adapter's own rules: statuses, errors, rate limits, paging, ids."""

import re
from datetime import UTC, datetime

import httpx
import pytest

from spoolhq.services.projects.model import StatusMap
from spoolhq.services.tracker.base import TrackerError
from spoolhq.services.tracker.clickup import ClickUpAdapter
from tests.services.tracker.fakes import TOKEN, FakeClickUp
from tests.services.tracker.test_contract import ticket

NOW = datetime(2026, 11, 21, 9, 0, tzinfo=UTC)


def adapter(server: FakeClickUp, status_map: StatusMap | None = None) -> ClickUpAdapter:
    return ClickUpAdapter(
        "123", status_map or StatusMap(), TOKEN, transport=server.transport, clock=lambda: NOW
    )


def test_requests_go_to_the_fixed_host_with_the_token_header() -> None:
    server = FakeClickUp()
    adapter(server).push_ticket(ticket())
    assert {str(r.url).split("/api/v2/")[0] for r in server.requests} == {"https://api.clickup.com"}
    assert all(r.headers["Authorization"] == TOKEN for r in server.requests)


def test_a_status_the_list_lacks_fails_with_the_fixed_message() -> None:
    server = FakeClickUp(statuses=["Open", "Doing", "Closed"])
    with pytest.raises(TrackerError) as caught:
        adapter(server).push_ticket(ticket())
    assert str(caught.value) == ("ClickUp list has no status 'to do'; set tracker.status_map.draft")
    assert server.writes() == []


def test_statuses_compare_case_insensitively_and_use_the_lists_spelling() -> None:
    server = FakeClickUp(statuses=["Open", "Doing", "Closed"])
    names = {"draft": "open", "ready": "OPEN", "running": "doing"}
    status_map = StatusMap(**names, awaiting_approval="doing", blocked="doing", done="closed")
    ref = adapter(server, status_map).push_ticket(ticket())
    assert server.tasks[ref].status == "Open"


@pytest.mark.parametrize(
    ("fail", "message"),
    [
        (500, "ClickUp answered 500"),
        (401, "ClickUp rejected the token (401)"),
        (302, "ClickUp answered 302"),
        ("timeout", "ClickUp timed out"),
    ],
)
def test_failures_have_fixed_messages(fail: int | str, message: str) -> None:
    server = FakeClickUp()
    server.fail = fail
    with pytest.raises(TrackerError, match=re.escape(message)) as caught:
        adapter(server).push_ticket(ticket())
    assert caught.value.retry_after is None
    assert TOKEN not in str(caught.value)


def test_a_redirect_is_not_followed() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert request.url.host == "api.clickup.com"
        return httpx.Response(301, headers={"Location": "https://evil.example/steal"})

    seen = ClickUpAdapter("123", StatusMap(), TOKEN, transport=httpx.MockTransport(handle))
    with pytest.raises(TrackerError, match="ClickUp answered 301"):
        seen.comment("abc", "x")


def test_unreachable() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    seen = ClickUpAdapter("123", StatusMap(), TOKEN, transport=httpx.MockTransport(handle))
    with pytest.raises(TrackerError, match="Couldn't reach ClickUp"):
        seen.comment("abc", "x")


@pytest.mark.parametrize(
    ("reset", "wait"),
    [(str(NOW.timestamp() + 42), 42.0), (str((NOW.timestamp() + 7) * 1000), 7.0), ("x", 60.0)],
)
def test_a_rate_limit_says_how_long_to_wait(reset: str, wait: float) -> None:
    server = FakeClickUp()
    server.rate_limit = reset
    with pytest.raises(TrackerError) as caught:
        adapter(server).comment("abc", "x")
    assert caught.value.retry_after == pytest.approx(wait)


def test_an_unreadable_answer() -> None:
    seen = ClickUpAdapter(
        "123",
        StatusMap(),
        TOKEN,
        transport=httpx.MockTransport(lambda r: httpx.Response(200, content=b"<html>")),
    )
    with pytest.raises(TrackerError, match="unreadable"):
        seen.comment("abc", "x")


def test_a_ref_that_is_not_an_id_is_refused_before_any_call() -> None:
    server = FakeClickUp()
    with pytest.raises(TrackerError, match="is not a ClickUp id"):
        adapter(server).comment("../user", "x")
    assert server.requests == []


def test_finding_a_task_reads_every_page_once() -> None:
    server = FakeClickUp(page_size=2)
    for number in range(1, 6):
        server.add_task(f"T{number:02d} · Ticket {number}")
    seen = adapter(server)

    assert seen.push_ticket(ticket("T05")) == "t5"
    assert seen.push_ticket(ticket("T06")) == "t6"  # created, no second scan
    pages = [r.url.params["page"] for r in server.requests if "page" in r.url.params]
    assert pages == ["0", "1", "2"]
