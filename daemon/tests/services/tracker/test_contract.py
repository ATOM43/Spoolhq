"""The contract every tracker adapter passes (like T27's for agent backends): run against
the ClickUp adapter on the fake API and against the in-memory test adapter."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass

import pytest

from spoolhq.services.projects.model import StatusMap, Tracker
from spoolhq.services.tickets import Ticket, parse_ticket
from spoolhq.services.tracker.base import FOOTER, TrackerAdapter
from spoolhq.services.tracker.registry import ADAPTERS, make_adapter
from tests.services.tracker.fakes import TOKEN, FakeClickUp, FakeTask, MemoryAdapter


def ticket(ticket_id: str = "T04", status: str = "ready", ref: str | None = None) -> Ticket:
    ref_line = f"tracker_ref: {ref}\n" if ref else ""
    text = (
        f"---\nid: {ticket_id}\ntitle: Project workspace\nphase: 1\nstatus: {status}\n"
        f"estimate_h: 2\n{ref_line}---\n\n## Scope\nMake it.\n\n## Done when\n- [ ] done\n"
    )
    return parse_ticket(text, f"{ticket_id}-project-workspace.md")


@dataclass
class Subject:
    adapter: TrackerAdapter
    tasks: Callable[[], dict[str, FakeTask]]
    """Every task the tracker holds, by ref."""
    seed: Callable[[str], str]
    """Put a task with this name in the tracker (as a crash would leave it); its ref."""


def _clickup() -> Subject:
    server = FakeClickUp()
    tracker = Tracker(kind="clickup", list_id="123")
    return Subject(
        make_adapter(tracker, TOKEN, server.transport),
        lambda: server.tasks,
        lambda name: server.add_task(name).id,
    )


def _memory() -> Subject:
    adapter = MemoryAdapter()

    def seed(name: str) -> str:
        ref = f"m{len(adapter.tasks) + 1}"
        adapter.tasks[ref] = FakeTask(ref, name, "to do", "")
        return ref

    return Subject(adapter, lambda: adapter.tasks, seed)


@pytest.fixture(params=[_clickup, _memory], ids=["clickup", "memory"])
def subject(request: pytest.FixtureRequest) -> Iterator[Subject]:
    found: Subject = request.param()
    yield found
    found.adapter.close()


def test_every_kind_in_project_yaml_has_an_adapter() -> None:
    assert set(ADAPTERS) == {"clickup"} == set(Tracker.model_fields["kind"].annotation.__args__)  # type: ignore[union-attr]


def test_push_creates_once_then_updates(subject: Subject) -> None:
    ref = subject.adapter.push_ticket(ticket())
    again = subject.adapter.push_ticket(ticket(status="running", ref=ref))

    assert again == ref
    assert list(subject.tasks()) == [ref]
    task = subject.tasks()[ref]
    assert task.name == "T04 · Project workspace"
    assert task.status == "in progress"
    assert "## Done when" in task.markdown and FOOTER in task.markdown


def test_push_without_a_ref_adopts_the_task_named_after_the_ticket(subject: Subject) -> None:
    subject.seed("T40 · Another ticket")
    existing = subject.seed("T04 · Old title")

    assert subject.adapter.push_ticket(ticket()) == existing
    assert len(subject.tasks()) == 2
    assert subject.tasks()[existing].name == "T04 · Project workspace"


def test_status_maps_through_the_status_map(subject: Subject) -> None:
    ref = subject.adapter.push_ticket(ticket())
    for status, expected in StatusMap().model_dump().items():
        subject.adapter.update_status(ref, status)
        assert subject.tasks()[ref].status == expected


def test_comment_and_pull_request_link(subject: Subject) -> None:
    ref = subject.adapter.push_ticket(ticket())
    subject.adapter.comment(ref, "SpoolHQ run 1: done")
    subject.adapter.link_pr(ref, "https://github.com/o/r/pull/3")

    assert subject.tasks()[ref].comments == [
        "SpoolHQ run 1: done",
        "Pull request: https://github.com/o/r/pull/3",
    ]
