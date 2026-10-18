import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from spoolhq.services.tickets import (
    TICKET_STATUSES,
    DoneItem,
    TicketError,
    TicketValidationError,
    list_tickets,
    load_ticket,
    parse_done_when,
    parse_ticket,
    read_ticket,
    save_ticket,
)
from spoolhq.services.tickets import document as ticket_document

FIXTURES = Path(__file__).parent / "fixtures"
ROUND_TRIP = sorted(path.name for path in (FIXTURES / "tickets").glob("*.md"))

VALID_FRONTMATTER = """\
id: T04
title: Project workspace and settings
phase: 1
depends_on: [T02]
status: ready
estimate_h: 2
review_required: false
tracker_ref: null
"""
VALID_BODY = "\n## Scope\n- Something.\n\n## Done when\n- [ ] It works\n"
FILE_NAME = "T04-project-workspace.md"

# The dashboard plan: id -> (title, phase, depends_on, estimate_h).
DASHBOARD = {
    "T01": ("Repository and tooling", 0, [], 1),
    "T02": ("Backend scaffold", 0, ["T01"], 1),
    "T03": ("Frontend scaffold", 0, ["T02"], 1.5),
    "T04": ("Database layer and schema", 1, ["T02"], 2),
    "T05": ("Assessment logic", 1, ["T01"], 1.5),
    "T06": ("CSV parsing and validation", 1, ["T02"], 2),
    "T07": ("Ingestion and sync", 1, ["T04", "T05", "T06"], 3),
    "T08": ("Discovery and results API", 2, ["T07"], 2),
    "T09": ("Comparison API", 2, ["T08"], 2),
    "T10": ("Demands API", 2, ["T08"], 3),
    "T11": ("App shell and routing", 3, ["T03", "T08"], 2),
    "T12": ("Shared chart and verdict components", 3, ["T11"], 3),
    "T13": ("Revisions page", 3, ["T12"], 2.5),
    "T14": ("Compare page", 3, ["T12", "T09"], 3),
    "T15": ("Demands page and dialogs", 3, ["T12", "T10"], 3.5),
    "T16": ("Bad-data handling pass", 4, ["T13", "T14", "T15"], 1.5),
    "T17": ("Test completion", 4, ["T16"], 2),
    "T18": ("Documentation and handover", 4, ["T17"], 2),
}


def make_project(projects_dir: Path, files: dict[str, str | bytes], name: str = "demo") -> Path:
    tickets = projects_dir / name / "tickets"
    tickets.mkdir(parents=True)
    for file_name, content in files.items():
        data = content if isinstance(content, bytes) else content.encode("utf-8")
        (tickets / file_name).write_bytes(data)
    return tickets


def ticket_text(frontmatter: str = VALID_FRONTMATTER, body: str = VALID_BODY) -> str:
    return f"---\n{frontmatter}---\n{body}"


def replace_line(frontmatter: str, key: str, line: str | None) -> str:
    """``frontmatter`` with the line for ``key`` replaced (or removed if ``line`` is None)."""
    lines = frontmatter.splitlines(keepends=True)
    out = [
        (line + "\n" if line is not None else "") if old.startswith(f"{key}:") else old
        for old in lines
    ]
    return "".join(out)


def errors_for(projects_dir: Path, text: str, file_name: str = FILE_NAME) -> list[str]:
    make_project(projects_dir, {file_name: text})
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert listing.tickets == []
    assert [invalid.file_name for invalid in listing.invalid] == [file_name]
    return listing.invalid[0].errors


@pytest.fixture
def round_trip_tickets(projects_dir: Path) -> Path:
    """A copy of the round-trip fixtures as the tickets of project ``rt``."""
    tickets = projects_dir / "rt" / "tickets"
    shutil.copytree(FIXTURES / "tickets", tickets)
    return tickets


def ticket_id(file_name: str) -> str:
    return file_name.split("-", 1)[0]


# Round trip ---------------------------------------------------------------------------


@pytest.mark.parametrize("file_name", ROUND_TRIP)
def test_unchanged_ticket_saves_identical_bytes(
    projects_dir: Path, round_trip_tickets: Path, file_name: str
) -> None:
    path = round_trip_tickets / file_name
    before = path.read_bytes()
    ticket = load_ticket("rt", ticket_id(file_name), projects_dir=projects_dir)
    assert save_ticket("rt", ticket, projects_dir=projects_dir) == path
    assert path.read_bytes() == before
    # Fixtures are copied byte for byte, so this also checks git kept them intact.
    assert before == (FIXTURES / "tickets" / file_name).read_bytes()


@pytest.mark.parametrize("file_name", ROUND_TRIP)
def test_changing_status_changes_only_that_line(
    projects_dir: Path, round_trip_tickets: Path, file_name: str
) -> None:
    path = round_trip_tickets / file_name
    before = path.read_bytes().decode("utf-8")
    ticket = load_ticket("rt", ticket_id(file_name), projects_dir=projects_dir)
    old_status = ticket.meta.status
    new_status = "blocked" if old_status != "blocked" else "done"
    ticket.meta.status = new_status
    save_ticket("rt", ticket, projects_dir=projects_dir)

    old_lines = ticket_document.split_lines(before)
    new_lines = ticket_document.split_lines(path.read_bytes().decode("utf-8"))
    assert len(new_lines) == len(old_lines)
    changed = [
        i for i, (old, new) in enumerate(zip(old_lines, new_lines, strict=True)) if old != new
    ]
    assert len(changed) == 1
    old_line, new_line = old_lines[changed[0]], new_lines[changed[0]]
    assert old_line.lstrip("﻿").startswith("status:")
    # Same quoting, spacing, comment and line ending; only the value differs.
    assert new_line == old_line.replace(old_status, new_status, 1)
    assert read_ticket(path).meta.status == new_status


def save_and_read(projects_dir: Path, tickets: Path, file_name: str, **changes: object) -> str:
    ticket = load_ticket("rt", ticket_id(file_name), projects_dir=projects_dir)
    for key, value in changes.items():
        setattr(ticket.meta, key, value)
    save_ticket("rt", ticket, projects_dir=projects_dir)
    return (tickets / file_name).read_bytes().decode("utf-8")


def test_block_list_keeps_its_layout(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T06-block-lists.md", depends_on=["T01", "T02", "T03"]
    )
    assert "depends_on:   # block style, indented\n  - T01\n  - T02\n  - T03\nstatus:" in text


def test_unindented_block_list_keeps_its_layout(
    projects_dir: Path, round_trip_tickets: Path
) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T09-block-list-unindented.md", depends_on=["T05"]
    )
    assert "\ndepends_on:\n- T05\nstatus:" in text


def test_flow_list_stays_flow(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T07-flow-lists.md", depends_on=["T01", "T05", "T06"]
    )
    assert "\ndepends_on: [T01, T05, T06]   # flow style\nstatus: ready\n" in text


def test_empty_list_stays_flow(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(projects_dir, round_trip_tickets, "T01-comments.md", depends_on=["T09"])
    assert "\ndepends_on: [T09]  # none yet\n" in text


def test_emptied_block_list_becomes_flow(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(projects_dir, round_trip_tickets, "T06-block-lists.md", depends_on=[])
    assert "\ndepends_on: []   # block style, indented\nstatus: ready\n" in text


def test_quoted_values_keep_their_quotes(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(
        projects_dir,
        round_trip_tickets,
        "T08-quoting.md",
        title="Don't # stop",
        tracker_ref="CU-99",
        depends_on=["T01", "T03"],
    )
    assert "\ntitle: 'Don''t # stop'\n" in text
    assert "\ntracker_ref: 'CU-99'  # quoted\n" in text
    assert '\ndepends_on: ["T01", "T03"]\n' in text
    assert read_ticket(round_trip_tickets / "T08-quoting.md").meta.title == "Don't # stop"


def test_double_quoted_escapes_do_not_hide_the_comment(projects_dir: Path) -> None:
    frontmatter = replace_line(
        VALID_FRONTMATTER, "title", 'title: "say \\"hi\\" # here"  # real comment'
    )
    tickets = make_project(projects_dir, {FILE_NAME: ticket_text(frontmatter)})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    assert ticket.meta.title == 'say "hi" # here'
    ticket.meta.title = "New"
    save_ticket("demo", ticket, projects_dir=projects_dir)
    assert '\ntitle: "New"  # real comment\n' in (tickets / FILE_NAME).read_text("utf-8")


def test_plain_value_gets_quotes_only_when_needed(
    projects_dir: Path, round_trip_tickets: Path
) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T01-comments.md", title="Fix: the colon"
    )
    assert "\ntitle: 'Fix: the colon'\n" in text


def test_value_set_to_null(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(projects_dir, round_trip_tickets, "T08-quoting.md", tracker_ref=None)
    assert "\ntracker_ref: null  # quoted\n" in text


def test_new_key_is_appended_with_the_files_line_ending(
    projects_dir: Path, round_trip_tickets: Path
) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T02-crlf.md", review_required=True, estimate_h=3.0
    )
    assert "estimate_h: 3\r\nreview_required: true\r\n---\r\n" in text
    assert "\n" not in text.replace("\r\n", "")


def test_new_key_in_frontmatter_only_file(projects_dir: Path, round_trip_tickets: Path) -> None:
    text = save_and_read(
        projects_dir, round_trip_tickets, "T11-frontmatter-only.md", tracker_ref="X-1"
    )
    assert text.endswith("estimate_h: 1\ntracker_ref: X-1\n---")


def test_body_is_written_verbatim(projects_dir: Path, round_trip_tickets: Path) -> None:
    ticket = load_ticket("rt", "T03", projects_dir=projects_dir)
    ticket.body += "\n- [ ] Another item"
    save_ticket("rt", ticket, projects_dir=projects_dir)
    text = (round_trip_tickets / "T03-no-final-newline.md").read_text("utf-8")
    assert text.endswith("- [ ] The missing newline stays missing\n- [ ] Another item")


def test_second_save_builds_on_the_first(projects_dir: Path, round_trip_tickets: Path) -> None:
    ticket = load_ticket("rt", "T01", projects_dir=projects_dir)
    ticket.meta.status = "running"
    save_ticket("rt", ticket, projects_dir=projects_dir)
    ticket.meta.phase = 2
    save_ticket("rt", ticket, projects_dir=projects_dir)
    text = (round_trip_tickets / "T01-comments.md").read_text("utf-8")
    assert "\nphase: 2 # phase comment\n" in text
    assert "\nstatus: running  # draft |" in text


def test_flow_mapping_frontmatter_is_re_rendered(projects_dir: Path) -> None:
    text = "---\n{id: T04, title: X, phase: 1, status: ready, estimate_h: 2}\n---\nBody\n"
    tickets = make_project(projects_dir, {FILE_NAME: text})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    save_ticket("demo", ticket, projects_dir=projects_dir)
    assert (tickets / FILE_NAME).read_text("utf-8") == text

    ticket.meta.status = "done"
    save_ticket("demo", ticket, projects_dir=projects_dir)
    saved = read_ticket(tickets / FILE_NAME)
    assert saved.meta.status == "done"
    assert saved.meta.title == "X"
    assert saved.body == "Body\n"


def test_unexpected_splice_falls_back_to_full_render(
    projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tickets = make_project(projects_dir, {FILE_NAME: ticket_text().replace("\n", "\r\n")})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    monkeypatch.setattr(ticket_document, "_splice", lambda text, changes: "id: [broken\n")
    ticket.meta.status = "done"
    save_ticket("demo", ticket, projects_dir=projects_dir)
    raw = (tickets / FILE_NAME).read_bytes().decode("utf-8")
    assert "\r\nstatus: done\r\n" in raw
    assert "\n" not in raw.replace("\r\n", "")
    assert read_ticket(tickets / FILE_NAME).meta.status == "done"


def test_save_validates_values_set_without_validation(projects_dir: Path) -> None:
    tickets = make_project(projects_dir, {FILE_NAME: ticket_text()})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    ticket.meta = ticket.meta.model_copy(update={"estimate_h": 99, "id": "T05"})
    with pytest.raises(TicketValidationError) as info:
        save_ticket("demo", ticket, projects_dir=projects_dir)
    assert info.value.errors == [
        f"tickets/{FILE_NAME}: id: 'T05' does not match the file name prefix 'T04'",
        f"tickets/{FILE_NAME}: estimate_h: must be at most 40",
    ]
    assert (tickets / FILE_NAME).read_text("utf-8") == ticket_text()


def test_assignment_is_validated(projects_dir: Path) -> None:
    make_project(projects_dir, {FILE_NAME: ticket_text()})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    with pytest.raises(ValidationError):
        ticket.meta.status = "doing"  # type: ignore[assignment]


def test_save_without_tickets_folder(projects_dir: Path) -> None:
    tickets = make_project(projects_dir, {FILE_NAME: ticket_text()})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    shutil.rmtree(tickets)
    with pytest.raises(TicketError, match="no tickets folder in project 'demo'"):
        save_ticket("demo", ticket, projects_dir=projects_dir)


# The dashboard plan -------------------------------------------------------------------


def test_dashboard_plan_loads() -> None:
    listing = list_tickets("dashboard", projects_dir=FIXTURES)
    assert listing.invalid == []
    assert [ticket.id for ticket in listing.tickets] == list(DASHBOARD)
    for ticket in listing.tickets:
        title, phase, depends_on, estimate_h = DASHBOARD[ticket.id]
        assert ticket.meta.title == title
        assert ticket.meta.phase == phase
        assert ticket.meta.depends_on == depends_on
        assert ticket.meta.estimate_h == estimate_h
        assert ticket.meta.status == "ready"
        assert ticket.meta.review_required is False
        assert ticket.meta.tracker_ref is None
        assert ticket.done_when, ticket.id
        assert ticket.warnings == []
        assert "## Scope\n- " in ticket.body
    assert sum(ticket.meta.estimate_h for ticket in listing.tickets) == 38.5


@pytest.mark.parametrize(
    ("status", "phase", "expected"),
    [
        ("ready", None, list(DASHBOARD)),
        ("done", None, []),
        (None, 0, ["T01", "T02", "T03"]),
        (None, 3, ["T11", "T12", "T13", "T14", "T15"]),
        ("ready", 4, ["T16", "T17", "T18"]),
        ("blocked", 4, []),
        (None, 9, []),
    ],
)
def test_dashboard_filters(status: str | None, phase: int | None, expected: list[str]) -> None:
    listing = list_tickets("dashboard", projects_dir=FIXTURES, status=status, phase=phase)
    assert [ticket.id for ticket in listing.tickets] == expected


def test_unknown_status_filter() -> None:
    with pytest.raises(TicketError, match="unknown status 'doing'; expected one of: draft"):
        list_tickets("dashboard", projects_dir=FIXTURES, status="doing")


# Frontmatter rules --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("key", "line", "message"),
    [
        ("id", "id: T4", "id: must be T followed by 2 or 3 digits, like T04"),
        ("id", "id: T05", "id: 'T05' does not match the file name prefix 'T04'"),
        ("title", "title: '  '", "title: must not be empty"),
        ("title", None, "title: field required"),
        ("phase", "phase: -1", "phase: must be at least 0"),
        ("phase", "phase: '1'", "phase: input should be a valid integer"),
        (
            "status",
            "status: doing",
            "status: must be one of draft, ready, running, awaiting_approval, blocked, done",
        ),
        ("depends_on", "depends_on: [T04]", "depends_on: T04 cannot depend on itself"),
        ("depends_on", "depends_on: [T01, T01]", "depends_on: T01 is listed more than once"),
        (
            "depends_on",
            "depends_on: [t1]",
            "depends_on: 't1' is not a ticket id (must be T followed by 2 or 3 digits, like T04)",
        ),
        ("depends_on", "depends_on: T01", "depends_on: input should be a valid list"),
        ("estimate_h", "estimate_h: 0", "estimate_h: must be greater than 0"),
        ("estimate_h", "estimate_h: 40.5", "estimate_h: must be at most 40"),
        ("estimate_h", "estimate_h: .inf", "estimate_h: input should be a finite number"),
        (
            "review_required",
            "review_required: yes",
            "review_required: input should be a valid boolean",
        ),
        ("tracker_ref", "tracker_ref: 5", "tracker_ref: input should be a valid string"),
        ("tracker_ref", "stauts: ready", "stauts: unknown key (did you mean 'status'?)"),
        ("tracker_ref", "colour: blue", "colour: unknown key"),
    ],
)
def test_frontmatter_rule(projects_dir: Path, key: str, line: str | None, message: str) -> None:
    frontmatter = replace_line(VALID_FRONTMATTER, key, line)
    assert errors_for(projects_dir, ticket_text(frontmatter)) == [f"tickets/{FILE_NAME}: {message}"]


def test_every_error_is_reported_at_once(projects_dir: Path) -> None:
    frontmatter = "id: T4\nphase: -2\nstatus: doing\nestimate_h: 50\nextra: 1\n"
    prefix = f"tickets/{FILE_NAME}: "
    assert errors_for(projects_dir, ticket_text(frontmatter)) == [
        prefix + "id: must be T followed by 2 or 3 digits, like T04",
        prefix + "title: field required",
        prefix + "phase: must be at least 0",
        prefix + "status: must be one of draft, ready, running, awaiting_approval, blocked, done",
        prefix + "estimate_h: must be at most 40",
        prefix + "extra: unknown key",
    ]


def test_three_digit_ids(projects_dir: Path) -> None:
    frontmatter = replace_line(VALID_FRONTMATTER, "id", "id: T104")
    make_project(projects_dir, {"T104-big.md": ticket_text(frontmatter)})
    assert load_ticket("demo", "T104", projects_dir=projects_dir).id == "T104"


def test_bad_file_name(projects_dir: Path) -> None:
    assert errors_for(projects_dir, ticket_text(), "notes.md") == [
        "tickets/notes.md: file name must be <id>-<slug>.md, like T04-project-workspace.md"
    ]


def test_lowercase_file_prefix_does_not_match(projects_dir: Path) -> None:
    assert errors_for(projects_dir, ticket_text(), "t04-x.md") == [
        "tickets/t04-x.md: id: 'T04' does not match the file name prefix 't04'"
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("# Title\n", "line 1: the file must start with a '---' line opening the frontmatter"),
        ("", "line 1: the file must start with a '---' line opening the frontmatter"),
        ("---\nid: T04\n", "the frontmatter is not closed: add a '---' line after it"),
        ("---\n---\nbody\n", "the frontmatter is empty"),
        ("---\n- a\n---\n", "the frontmatter must be a mapping of fields"),
        (
            "---\nid: T04\ntitle: [unclosed\nphase: 1\n---\n",
            "line 4, column 6: expected ',' or ']', but got ':'",
        ),
        (
            "---\nid: T04\nid: T05\n---\n",
            'line 3, column 1: found duplicate key "id" with value "T05" (original value: "T04")',
        ),
        ("---\nid: T04\ntitle: a\x07b\n---\n", "line 3, column 9: unacceptable character #x0007"),
        (
            "---\n\tid: T04\n---\n",
            "line 2, column 1: found character '\\t' that cannot start any token",
        ),
    ],
)
def test_file_structure_errors(projects_dir: Path, text: str, message: str) -> None:
    assert errors_for(projects_dir, text) == [f"tickets/{FILE_NAME}: {message}"]


def test_unsafe_tag_is_plain_data(projects_dir: Path) -> None:
    frontmatter = replace_line(
        VALID_FRONTMATTER, "title", "title: !!python/object/apply:os.system ['echo hi']"
    )
    assert errors_for(projects_dir, ticket_text(frontmatter)) == [
        f"tickets/{FILE_NAME}: title: input should be a valid string"
    ]


def test_not_utf8(projects_dir: Path) -> None:
    make_project(projects_dir, {FILE_NAME: b"---\nid: T04\ntitle: caf\xe9\n---\n"})
    with pytest.raises(TicketValidationError) as info:
        load_ticket("demo", "T04", projects_dir=projects_dir)
    assert info.value.errors == [f"tickets/{FILE_NAME}: not UTF-8 text (invalid byte at offset 22)"]


def test_crlf_frontmatter_errors_count_lines(projects_dir: Path) -> None:
    text = "---\r\nid: T04\r\nid: T05\r\n---\r\n"
    assert errors_for(projects_dir, text)[0].startswith(f"tickets/{FILE_NAME}: line 3, column 1:")


# The store ----------------------------------------------------------------------------


def test_broken_file_does_not_stop_the_others(projects_dir: Path) -> None:
    other = replace_line(VALID_FRONTMATTER, "id", "id: T01")
    make_project(
        projects_dir,
        {
            "T01-first.md": ticket_text(other),
            "T02-broken.md": "---\nid: T02\nstatus: [\n---\n",
            FILE_NAME: ticket_text(),
        },
    )
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert [ticket.id for ticket in listing.tickets] == ["T01", "T04"]
    assert [invalid.file_name for invalid in listing.invalid] == ["T02-broken.md"]
    assert listing.invalid[0].errors[0].startswith("tickets/T02-broken.md: line 4, column 1:")


def test_folders_are_ignored(projects_dir: Path) -> None:
    tickets = make_project(projects_dir, {FILE_NAME: ticket_text()})
    (tickets / "T05-folder.md").mkdir()
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert [ticket.id for ticket in listing.tickets] == ["T04"]
    assert listing.invalid == []


def test_read_errors_become_invalid_entries(
    projects_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    make_project(projects_dir, {FILE_NAME: ticket_text()})

    def broken(self: Path) -> bytes:
        raise PermissionError("denied")

    monkeypatch.setattr(Path, "read_bytes", broken)
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert listing.invalid[0].errors[0].startswith(f"tickets/{FILE_NAME}: cannot read ")


def test_read_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TicketError, match="not found at"):
        read_ticket(tmp_path / FILE_NAME)


def test_hidden_and_other_files_are_ignored(projects_dir: Path) -> None:
    make_project(
        projects_dir,
        {
            FILE_NAME: ticket_text(),
            f".{FILE_NAME}.bak": "junk",
            ".T09-hidden.md": "junk",
            "README.txt": "junk",
        },
    )
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert [ticket.id for ticket in listing.tickets] == ["T04"]
    assert listing.invalid == []


def test_tickets_sorted_by_number(projects_dir: Path) -> None:
    files = {}
    for number in ("T100", "T02", "T10", "T99"):
        frontmatter = replace_line(VALID_FRONTMATTER, "id", f"id: {number}")
        frontmatter = replace_line(frontmatter, "depends_on", None)
        files[f"{number}-x.md"] = ticket_text(frontmatter)
    make_project(projects_dir, files)
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert [ticket.id for ticket in listing.tickets] == ["T02", "T10", "T99", "T100"]


def test_project_without_tickets_folder(projects_dir: Path) -> None:
    (projects_dir / "demo").mkdir(parents=True)
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert listing.tickets == [] and listing.invalid == []


def test_missing_project(projects_dir: Path) -> None:
    with pytest.raises(TicketError, match=f"no project 'nope' in {projects_dir}"):
        list_tickets("nope", projects_dir=projects_dir)


def test_bad_project_name(projects_dir: Path) -> None:
    with pytest.raises(TicketError, match="invalid project name '../x'"):
        list_tickets("../x", projects_dir=projects_dir)


def test_load_ticket_errors(projects_dir: Path) -> None:
    make_project(projects_dir, {FILE_NAME: ticket_text(), "T04-copy.md": ticket_text()})
    with pytest.raises(TicketError, match="no ticket T09 in project 'demo'"):
        load_ticket("demo", "T09", projects_dir=projects_dir)
    with pytest.raises(TicketError, match="invalid ticket id 'x'"):
        load_ticket("demo", "x", projects_dir=projects_dir)
    with pytest.raises(
        TicketError,
        match=f"more than one file for T04: tickets/T04-copy.md, tickets/{FILE_NAME}",
    ):
        load_ticket("demo", "T04", projects_dir=projects_dir)


def test_load_invalid_ticket(projects_dir: Path) -> None:
    frontmatter = replace_line(VALID_FRONTMATTER, "status", "status: doing")
    make_project(projects_dir, {FILE_NAME: ticket_text(frontmatter)})
    with pytest.raises(TicketValidationError, match="status: must be one of"):
        load_ticket("demo", "T04", projects_dir=projects_dir)


def test_parse_ticket_parts() -> None:
    ticket = parse_ticket(ticket_text(), FILE_NAME)
    assert ticket.id == "T04"
    assert ticket.file_name == FILE_NAME
    assert ticket.body == VALID_BODY
    assert ticket.meta.model_dump() == {
        "id": "T04",
        "title": "Project workspace and settings",
        "phase": 1,
        "depends_on": ["T02"],
        "status": "ready",
        "estimate_h": 2.0,
        "review_required": False,
        "tracker_ref": None,
    }
    assert ticket.done_when == [DoneItem(text="It works", checked=False)]


def test_defaults_for_optional_fields() -> None:
    frontmatter = "id: T04\ntitle: X\nphase: 0\nstatus: draft\nestimate_h: 0.25\n"
    meta = parse_ticket(ticket_text(frontmatter), FILE_NAME).meta
    assert meta.depends_on == []
    assert meta.review_required is False
    assert meta.tracker_ref is None


def test_every_status_is_accepted() -> None:
    for status in TICKET_STATUSES:
        frontmatter = replace_line(VALID_FRONTMATTER, "status", f"status: {status}")
        assert parse_ticket(ticket_text(frontmatter), FILE_NAME).meta.status == status


# Done when ----------------------------------------------------------------------------


def test_done_when_items() -> None:
    body = (
        "## Scope\n- [ ] not in Done when\n\n"
        "## Done when\n- [ ] Open\n- [x] Done\n* [X] Star and capital X\n+ [ ]\n"
        "  - [ ] Nested\nNot an item\n- plain bullet\n\n"
        "### Sub-heading\n- [ ] Still in the section\n\n"
        "## Notes\n- [ ] Not in Done when\n"
    )
    items, warnings = parse_done_when(body)
    assert items == [
        DoneItem(text="Open", checked=False),
        DoneItem(text="Done", checked=True),
        DoneItem(text="Star and capital X", checked=True),
        DoneItem(text="", checked=False),
        DoneItem(text="Nested", checked=False),
        DoneItem(text="Still in the section", checked=False),
    ]
    assert warnings == []


def test_done_when_heading_variants() -> None:
    body = "# Ticket\r\n### Done When ###\r\n- [x] CRLF item  \r\n# Next\r\n- [ ] after\r\n"
    assert parse_done_when(body) == ([DoneItem(text="CRLF item", checked=True)], [])


def test_done_when_ignores_code_fences() -> None:
    body = (
        "```\n## Done when\n- [ ] fenced\n```\n"
        "## Done when\n- [ ] real\n~~~~\n- [ ] fenced too\n~~~\n- [ ] still fenced\n~~~~\n"
        "- [x] after the fence\n"
    )
    items, _ = parse_done_when(body)
    assert items == [
        DoneItem(text="real", checked=False),
        DoneItem(text="after the fence", checked=True),
    ]


def test_missing_done_when_is_a_warning(projects_dir: Path) -> None:
    make_project(projects_dir, {FILE_NAME: ticket_text(body="\n## Scope\n- x\n")})
    ticket = load_ticket("demo", "T04", projects_dir=projects_dir)
    assert ticket.done_when == []
    assert ticket.warnings == [f"tickets/{FILE_NAME}: no '## Done when' section"]


def test_empty_done_when_is_a_warning() -> None:
    assert parse_done_when("## Done when\n\nNothing yet.\n") == (
        [],
        ["the '## Done when' section has no checklist items"],
    )


def test_round_trip_fixture_checklists(projects_dir: Path, round_trip_tickets: Path) -> None:
    ticket = load_ticket("rt", "T05", projects_dir=projects_dir)
    assert ticket.done_when == [
        DoneItem(text="First criterion", checked=False),
        DoneItem(text="Second criterion", checked=True),
        DoneItem(text="A nested criterion", checked=False),
        DoneItem(text="A star bullet", checked=False),
        DoneItem(text="An item under a sub-heading", checked=False),
    ]
    unicode = load_ticket("rt", "T04", projects_dir=projects_dir)
    assert unicode.meta.title == "Ünïcödé — 日本語, emoji 🚀 and café"
    assert unicode.done_when[1] == DoneItem(text="絵文字 🎉 in an item", checked=True)
