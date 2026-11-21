"""The ClickUp adapter: a project is a list, a ticket a task named ``T04 · <title>``.

HTTPS to ``api.clickup.com`` only, no redirects, 10 s timeout, the personal token in the
``Authorization`` header (ClickUp API v2, checked 2026-11-21; docs/tracker.md). Before
its first write the adapter reads the list's statuses and refuses a ``status_map``
naming one the list doesn't have.
"""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx

from spoolhq.services.projects.model import StatusMap
from spoolhq.services.tickets import Ticket
from spoolhq.services.tracker.base import TrackerError, description, task_name, task_prefix

API = "https://api.clickup.com/api/v2"
TIMEOUT_S = 10.0
DEFAULT_WAIT_S = 60.0
MAX_WAIT_S = 3600.0
MAX_PAGES = 100
"""Pages of 100 tasks read when looking for a task by its name."""
ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")


def _check_id(value: str, what: str) -> str:
    """Ids go into URL paths; a ``tracker_ref`` comes from a ticket file."""
    if not ID_RE.fullmatch(value):
        raise TrackerError(f"{what} {value!r} is not a ClickUp id")
    return value


class ClickUpAdapter:
    def __init__(
        self,
        list_id: str,
        status_map: StatusMap,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.list_id = list_id
        self.status_map = status_map
        self.clock = clock
        self._client = httpx.Client(
            base_url=API,
            timeout=TIMEOUT_S,
            follow_redirects=False,
            trust_env=False,
            headers={"Authorization": token, "User-Agent": "spoolhq"},
            transport=transport,
        )
        self._statuses: dict[str, str] | None = None
        """Each mapped ticket status → the list's own spelling of its tracker status."""
        self._tasks: dict[str, str] | None = None
        """Ticket id → task id, from the task names in the list (crash recovery)."""

    def close(self) -> None:
        self._client.close()

    # TrackerAdapter -------------------------------------------------------------------

    def push_ticket(self, ticket: Ticket) -> str:
        body = {
            "name": task_name(ticket),
            "markdown_content": description(ticket),
            "status": self._status(ticket.meta.status),
        }
        ref = ticket.meta.tracker_ref or self._find(ticket.id)
        if ref is not None:
            self._request("PUT", f"/task/{_check_id(ref, 'tracker_ref')}", json=body)
            return ref
        list_id = _check_id(self.list_id, "tracker.list_id")
        created = str(self._request("POST", f"/list/{list_id}/task", json=body)["id"])
        assert self._tasks is not None  # noqa: S101 - _find loaded it
        self._tasks[ticket.id] = created
        return created

    def update_status(self, ref: str, status: str) -> None:
        body = {"status": self._status(status)}
        self._request("PUT", f"/task/{_check_id(ref, 'tracker_ref')}", json=body)

    def comment(self, ref: str, text: str) -> None:
        body = {"comment_text": text, "notify_all": False}
        self._request("POST", f"/task/{_check_id(ref, 'tracker_ref')}/comment", json=body)

    def link_pr(self, ref: str, url: str) -> None:
        self.comment(ref, f"Pull request: {url}")

    # Helpers --------------------------------------------------------------------------

    def _status(self, ticket_status: str) -> str:
        if self._statuses is None:
            list_id = _check_id(self.list_id, "tracker.list_id")
            found = self._request("GET", f"/list/{list_id}").get("statuses") or []
            names = {str(s.get("status", "")).lower(): str(s.get("status")) for s in found}
            statuses = {}
            for field, wanted in self.status_map.model_dump().items():
                if wanted.lower() not in names:
                    raise TrackerError(
                        f"ClickUp list has no status '{wanted}'; set tracker.status_map.{field}"
                    )
                statuses[field] = names[wanted.lower()]
            self._statuses = statuses
        return self._statuses[ticket_status]

    def _find(self, ticket_id: str) -> str | None:
        """The task whose name starts with ``T04 · ``, closed ones included. The list is
        read once per adapter; tasks it creates are added."""
        if self._tasks is None:
            list_id = _check_id(self.list_id, "tracker.list_id")
            tasks: dict[str, str] = {}
            for page in range(MAX_PAGES):
                params = {"page": page, "include_closed": "true"}
                data = self._request("GET", f"/list/{list_id}/task", params=params)
                for task in data.get("tasks") or []:
                    name, task_id = str(task.get("name", "")), str(task.get("id", ""))
                    prefix = name.split(" · ", 1)[0]
                    if name.startswith(task_prefix(prefix)) and task_id:
                        tasks.setdefault(prefix, task_id)
                if data.get("last_page", True) or not data.get("tasks"):
                    break
            self._tasks = tasks
        return self._tasks.get(ticket_id)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException:
            raise TrackerError("ClickUp timed out") from None
        except httpx.HTTPError:
            raise TrackerError("Couldn't reach ClickUp") from None
        status = response.status_code
        if status == 429:
            raise TrackerError("ClickUp rate limit", retry_after=self._wait(response))
        if status in (401, 403):
            raise TrackerError(f"ClickUp rejected the token ({status})")
        if not response.is_success:
            raise TrackerError(f"ClickUp answered {status}")
        try:
            data = response.json()
        except ValueError:
            raise TrackerError("ClickUp sent an unreadable answer") from None
        if not isinstance(data, dict):
            raise TrackerError("ClickUp sent an unreadable answer")
        return data

    def _wait(self, response: httpx.Response) -> float:
        """Seconds until ``X-RateLimit-Reset`` (a Unix time; milliseconds accepted)."""
        try:
            reset = float(response.headers["X-RateLimit-Reset"])
        except (KeyError, ValueError):
            return DEFAULT_WAIT_S
        if reset > 1e12:
            reset /= 1000
        return min(max(reset - self.clock().timestamp(), 1.0), MAX_WAIT_S)
