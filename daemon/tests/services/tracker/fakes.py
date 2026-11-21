"""A fake ClickUp API behind ``httpx.MockTransport``, and an in-memory adapter: what the
contract suite and the sync tests run against. Nothing here touches the network."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import httpx

from spoolhq.services.projects.model import StatusMap
from spoolhq.services.tickets import Ticket
from spoolhq.services.tracker.base import description, task_name, task_prefix

TOKEN = "pk_test_SECRET_token_0123456789"  # noqa: S105 - a fake token the tests scan for
DEFAULT_STATUSES = ["to do", "in progress", "complete"]


@dataclass
class FakeTask:
    id: str
    name: str
    status: str
    markdown: str
    comments: list[str] = field(default_factory=list)


class FakeClickUp:
    """One list (``123``). ``fail`` makes every call answer that status (or raise a
    timeout with ``"timeout"``); ``rate_limit`` answers the next call 429 with that
    ``X-RateLimit-Reset``. ``requests`` records every call."""

    def __init__(self, statuses: list[str] | None = None, page_size: int = 100) -> None:
        self.statuses = statuses or list(DEFAULT_STATUSES)
        self.page_size = page_size
        self.tasks: dict[str, FakeTask] = {}
        self.requests: list[httpx.Request] = []
        self.fail: int | str | None = None
        self.rate_limit: str | None = None
        self.on_request: Callable[[httpx.Request], None] | None = None
        self._next = 1

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    def add_task(self, name: str, status: str = "to do") -> FakeTask:
        task = FakeTask(f"t{self._next}", name, status, "")
        self._next += 1
        self.tasks[task.id] = task
        return task

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.on_request is not None:
            self.on_request(request)
        assert request.url.scheme == "https"
        assert request.url.host == "api.clickup.com"
        if request.headers.get("Authorization") != TOKEN:
            return httpx.Response(401, json={"err": "Token invalid"})
        if self.fail == "timeout":
            raise httpx.ReadTimeout("timed out", request=request)
        if isinstance(self.fail, int):
            return httpx.Response(self.fail, json={"err": "down"})
        if self.rate_limit is not None:
            reset, self.rate_limit = self.rate_limit, None
            return httpx.Response(429, headers={"X-RateLimit-Reset": reset}, json={})
        return self._route(request)

    def _route(self, request: httpx.Request) -> httpx.Response:
        parts = request.url.path.removeprefix("/api/v2/").split("/")
        body: dict[str, Any] = json.loads(request.content) if request.content else {}
        match request.method, parts:
            case "GET", ["list", "123"]:
                statuses = [{"status": s, "type": "open"} for s in self.statuses]
                return httpx.Response(200, json={"id": "123", "statuses": statuses})
            case "GET", ["list", "123", "task"]:
                assert request.url.params["include_closed"] == "true"
                page = int(request.url.params["page"])
                tasks = list(self.tasks.values())
                chunk = tasks[page * self.page_size : (page + 1) * self.page_size]
                last = (page + 1) * self.page_size >= len(tasks)
                found = [{"id": t.id, "name": t.name} for t in chunk]
                return httpx.Response(200, json={"tasks": found, "last_page": last})
            case "POST", ["list", "123", "task"]:
                task = self.add_task(body["name"], body["status"])
                task.markdown = body["markdown_content"]
                return httpx.Response(200, json={"id": task.id, "name": task.name})
            case "PUT", ["task", task_id] if task_id in self.tasks:
                task = self.tasks[task_id]
                task.name = body.get("name", task.name)
                task.status = body.get("status", task.status)
                task.markdown = body.get("markdown_content", task.markdown)
                return httpx.Response(200, json={"id": task.id})
            case "POST", ["task", task_id, "comment"] if task_id in self.tasks:
                assert body["notify_all"] is False
                self.tasks[task_id].comments.append(body["comment_text"])
                return httpx.Response(200, json={"id": "c1", "hist_id": "h1", "date": 0})
        return httpx.Response(404, json={"err": "not found"})

    def writes(self) -> list[httpx.Request]:
        return [r for r in self.requests if r.method != "GET"]


class MemoryAdapter:
    """A test adapter keeping tasks in memory, held to the same contract as ClickUp's."""

    def __init__(self, status_map: StatusMap | None = None) -> None:
        self.status_map = status_map or StatusMap()
        self.tasks: dict[str, FakeTask] = {}

    def push_ticket(self, ticket: Ticket) -> str:
        status = getattr(self.status_map, ticket.meta.status)
        ref = ticket.meta.tracker_ref or next(
            (t.id for t in self.tasks.values() if t.name.startswith(task_prefix(ticket.id))),
            None,
        )
        if ref is None:
            ref = f"m{len(self.tasks) + 1}"
            self.tasks[ref] = FakeTask(ref, "", "", "")
        task = self.tasks[ref]
        task.name, task.status, task.markdown = task_name(ticket), status, description(ticket)
        return ref

    def update_status(self, ref: str, status: str) -> None:
        self.tasks[ref].status = getattr(self.status_map, status)

    def comment(self, ref: str, text: str) -> None:
        self.tasks[ref].comments.append(text)

    def link_pr(self, ref: str, url: str) -> None:
        self.comment(ref, f"Pull request: {url}")

    def close(self) -> None:
        pass
