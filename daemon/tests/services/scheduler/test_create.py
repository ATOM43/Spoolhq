"""Saving the planner's drafts together: ids in draft order, refs rewritten, all files or
none."""

import threading
from pathlib import Path

import pytest

from spoolhq.services.scheduler import DraftTicket, TicketEditError, create_tickets
from spoolhq.services.scheduler import create as create_module
from spoolhq.services.tickets import list_tickets


def draft(ref: str, title: str, *deps: str) -> DraftTicket:
    return DraftTicket(
        ref=ref, title=title, done_when="- [ ] works", depends_on=list(deps), estimate_h=2
    )


def fill(workspace: Path, last: int, status: str = "ready") -> None:
    tickets = workspace / "tickets"
    tickets.mkdir(exist_ok=True)
    for n in range(1, last + 1):
        (tickets / f"T{n:02d}-t.md").write_text(
            f"---\nid: T{n:02d}\ntitle: T{n}\nphase: 2\ndepends_on: []\nstatus: {status}\n"
            "estimate_h: 1\n---\n\n## Done when\n- [ ] ok\n",
            encoding="utf-8",
        )


def names(workspace: Path) -> list[str]:
    return sorted(path.name for path in (workspace / "tickets").iterdir())


def test_refs_become_the_next_ids(workspace: Path, projects_dir: Path) -> None:
    fill(workspace, 45)
    saved = create_tickets(
        "demo",
        [draft("D1", "CSV export"), draft("D2", "CSV docs", "D1", "T45")],
        projects_dir=projects_dir,
    )
    assert [t.id for t in saved] == ["T46", "T47"]
    assert saved[1].meta.depends_on == ["T46", "T45"]
    assert (saved[0].meta.status, saved[0].meta.phase) == ("ready", 2)
    on_disk = {t.id: t for t in list_tickets("demo", projects_dir=projects_dir).tickets}
    assert on_disk["T47"].meta.depends_on == ["T46", "T45"]
    assert on_disk["T46"].file_name == "T46-csv-export.md"


def test_drafts_wait_with_a_draft_plan(workspace: Path, projects_dir: Path) -> None:
    fill(workspace, 2, status="draft")
    [saved] = create_tickets("demo", [draft("D1", "One")], projects_dir=projects_dir)
    assert saved.meta.status == "draft"


@pytest.mark.parametrize(
    ("drafts", "field", "message"),
    [
        ([draft("D1", "a"), draft("D2", "b", "T99")], "tickets.1.depends_on", "T99"),
        ([draft("D1", "a", "D2"), draft("D2", "b", "D1")], "tickets.0.depends_on", "cycle"),
        ([draft("D1", "a", "D3")], "tickets.0.depends_on", "D3, which does not exist"),
        ([draft("D1", "a"), draft("D1", "b")], "tickets.1.ref", "more than once"),
    ],
)
def test_one_invalid_draft_writes_no_files(
    workspace: Path, projects_dir: Path, drafts: list[DraftTicket], field: str, message: str
) -> None:
    fill(workspace, 3)
    with pytest.raises(TicketEditError, match=message) as caught:
        create_tickets("demo", drafts, projects_dir=projects_dir)
    assert caught.value.field == field
    assert names(workspace) == ["T01-t.md", "T02-t.md", "T03-t.md"]


def test_a_failed_write_removes_the_files_already_written(
    workspace: Path, projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fill(workspace, 1)
    real = create_module.write_atomic
    calls: list[Path] = []

    def flaky(path: Path, text: str) -> None:
        calls.append(path)
        if len(calls) == 2:
            raise OSError("disk full")
        real(path, text)

    monkeypatch.setattr(create_module, "write_atomic", flaky)
    with pytest.raises(OSError, match="disk full"):
        create_tickets("demo", [draft("D1", "a"), draft("D2", "b")], projects_dir=projects_dir)
    assert names(workspace) == ["T01-t.md"]


def test_two_batches_at_once_get_different_ids(workspace: Path, projects_dir: Path) -> None:
    fill(workspace, 1)
    results: list[list[str]] = []
    barrier = threading.Barrier(2)

    def save(title: str) -> None:
        barrier.wait()
        saved = create_tickets(
            "demo",
            [draft("D1", title), draft("D2", title + " 2", "D1")],
            projects_dir=projects_dir,
        )
        results.append([t.id for t in saved])

    threads = [threading.Thread(target=save, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(30)
    assert sorted(id_ for ids in results for id_ in ids) == ["T02", "T03", "T04", "T05"]
    assert len(names(workspace)) == 5
