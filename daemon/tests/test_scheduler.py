import re
import shutil
from pathlib import Path

import pytest

from spoolhq.services.scheduler import (
    TRANSITIONS,
    PlanError,
    PlanProblem,
    TransitionError,
    apply_transition,
    check_transition,
    critical_path,
    explain_idle,
    id_key,
    next_ready,
    parse_status,
    remaining_hours,
    summary,
    validate_plan,
    waiting_on,
)
from spoolhq.services.tickets import (
    TICKET_STATUSES,
    Ticket,
    TicketError,
    TicketStatus,
    list_tickets,
    load_ticket,
    parse_ticket,
)

FIXTURES = Path(__file__).parent / "fixtures"
DOCS = Path(__file__).parents[2] / "docs"


def make(
    ticket_id: str,
    deps: tuple[str, ...] = (),
    status: TicketStatus = "ready",
    estimate: float = 1,
    file_name: str | None = None,
    title: str | None = None,
) -> Ticket:
    """An in-memory ticket, parsed from text like a file."""
    text = (
        "---\n"
        f"id: {ticket_id}\n"
        f"title: {title or 'Ticket ' + ticket_id}\n"
        "phase: 0\n"
        f"depends_on: [{', '.join(deps)}]\n"
        f"status: {status}\n"
        f"estimate_h: {estimate}\n"
        "---\n\n## Done when\n- [ ] It works\n"
    )
    return parse_ticket(text, file_name or f"{ticket_id}-x.md")


def dashboard(done: tuple[str, ...] = ()) -> list[Ticket]:
    tickets = list_tickets("dashboard", projects_dir=FIXTURES).tickets
    for ticket in tickets:
        if ticket.id in done:
            ticket.meta.status = "done"
    return tickets


def messages(problems: list[PlanProblem]) -> list[str]:
    return [problem.message for problem in problems]


# Validation ---------------------------------------------------------------------------


def test_valid_plan_has_no_problems() -> None:
    assert validate_plan(dashboard()) == []
    assert validate_plan([]) == []


def test_unknown_dependency() -> None:
    problems = validate_plan([make("T06"), make("T07", ("T06", "T99"))])
    assert problems == [
        PlanProblem(
            "unknown_dependency", ("T07", "T99"), "T07 depends on T99, which does not exist"
        )
    ]


def test_three_ticket_cycle_lists_its_members_in_order() -> None:
    # Work order: T08 depends on T07, T09 on T08, and T07 on T09.
    tickets = [make("T09", ("T08",)), make("T07", ("T09",)), make("T08", ("T07",))]
    problems = validate_plan(tickets)
    assert problems == [PlanProblem("cycle", ("T07", "T08", "T09"), "cycle: T07 → T08 → T09 → T07")]


def test_cycle_starts_at_its_lowest_id_wherever_the_walk_enters() -> None:
    # T01 leads into the cycle T03 → T02 → T03... from T03, so the walk enters at T03.
    tickets = [make("T01"), make("T03", ("T01", "T02")), make("T02", ("T03",))]
    assert messages(validate_plan(tickets)) == ["cycle: T02 → T03 → T02"]


def test_two_separate_cycles_are_each_reported_once() -> None:
    tickets = [
        make("T01", ("T02",)),
        make("T02", ("T01",)),
        make("T03"),
        make("T04", ("T03", "T06")),
        make("T05", ("T04",)),
        make("T06", ("T05",)),
    ]
    assert messages(validate_plan(tickets)) == [
        "cycle: T01 → T02 → T01",
        "cycle: T04 → T05 → T06 → T04",
    ]


def test_overlapping_cycles_are_both_found() -> None:
    tickets = [make("T01", ("T02",)), make("T02", ("T01", "T03")), make("T03", ("T02",))]
    assert messages(validate_plan(tickets)) == [
        "cycle: T01 → T02 → T01",
        "cycle: T02 → T03 → T02",
    ]


def test_duplicate_id_names_both_files() -> None:
    tickets = [make("T04", file_name="T04-b.md"), make("T04", file_name="T04-a.md")]
    assert validate_plan(tickets) == [
        PlanProblem("duplicate_id", ("T04",), "T04 is defined in T04-a.md and T04-b.md")
    ]
    three = [*tickets, make("T04", file_name="T04-c.md")]
    assert messages(validate_plan(three)) == ["T04 is defined in T04-a.md, T04-b.md and T04-c.md"]


def test_all_problems_are_reported_at_once() -> None:
    tickets = [
        make("T01", ("T98",)),
        make("T02", ("T03",)),
        make("T03", ("T02", "T99")),
        make("T05", file_name="T05-a.md"),
        make("T05", file_name="T05-b.md"),
    ]
    assert [problem.code for problem in validate_plan(tickets)] == [
        "unknown_dependency",
        "unknown_dependency",
        "cycle",
        "duplicate_id",
    ]


def test_ids_sort_by_number() -> None:
    assert sorted(["T100", "T99", "T10", "T02"], key=id_key) == ["T02", "T10", "T99", "T100"]
    tickets = [make("T100", ("T999",)), make("T99", ("T998",))]
    assert messages(validate_plan(tickets)) == [
        "T99 depends on T998, which does not exist",
        "T100 depends on T999, which does not exist",
    ]
    assert next_ready([make("T100"), make("T99")]).id == "T99"  # type: ignore[union-attr]


# Transitions --------------------------------------------------------------------------

ALLOWED = [(old, new) for old, targets in TRANSITIONS.items() for new in targets]
DISALLOWED = [
    (old, new)
    for old in TICKET_STATUSES
    for new in TICKET_STATUSES
    if old != new and (old, new) not in ALLOWED
]


def test_the_table_matches_the_ticket() -> None:
    assert dict(TRANSITIONS) == {
        "draft": ("ready",),
        "ready": ("draft", "running"),
        "running": ("ready", "awaiting_approval", "blocked", "done"),
        "awaiting_approval": ("running", "blocked", "done"),
        "blocked": ("ready", "running"),
        "done": (),
    }


def test_the_docs_show_the_same_table() -> None:
    text = (DOCS / "scheduler.md").read_text(encoding="utf-8")
    text = text.split("## Status transitions", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| `(\w+)` \| (.*?) \|$", text, re.MULTILINE)
    documented = {old: tuple(re.findall(r"`(\w+)`", targets)) for old, targets in rows}
    assert documented == dict(TRANSITIONS)


@pytest.mark.parametrize(("old", "new"), ALLOWED)
def test_allowed_transitions_pass(old: TicketStatus, new: str) -> None:
    ticket = make("T02", ("T01",), status=old)
    check_transition(ticket, new, [make("T01", status="done"), ticket])


@pytest.mark.parametrize(("old", "new"), DISALLOWED)
def test_disallowed_transitions_raise(old: TicketStatus, new: str) -> None:
    ticket = make("T02", status=old)
    with pytest.raises(TransitionError, match=f"^T02: {old} → {new} is not allowed"):
        check_transition(ticket, new, [ticket])


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        (
            "blocked",
            "done",
            "T07: blocked → done is not allowed; from blocked a ticket can "
            "move to ready or running",
        ),
        (
            "draft",
            "running",
            "T07: draft → running is not allowed; from draft a ticket can move to ready",
        ),
        ("done", "ready", "T07: done → ready is not allowed; done is final"),
    ],
)
def test_disallowed_transition_messages(old: TicketStatus, new: str, message: str) -> None:
    ticket = make("T07", status=old)
    with pytest.raises(TransitionError) as exc:
        check_transition(ticket, new, [ticket])
    assert str(exc.value) == message


@pytest.mark.parametrize("status", TICKET_STATUSES)
def test_same_status_is_a_no_op(status: TicketStatus) -> None:
    # Even running -> running with unmet dependencies: nothing changes, nothing is checked.
    ticket = make("T07", ("T04",), status=status)
    check_transition(ticket, status, [make("T04", status="draft"), ticket])


def test_unknown_status_is_refused() -> None:
    with pytest.raises(TransitionError, match="unknown status 'doing'; expected one of: draft"):
        check_transition(make("T01"), "doing", [])
    assert parse_status("done") == "done"


def test_running_waits_for_every_dependency() -> None:
    plan = [
        make("T04", status="running"),
        make("T05", status="done"),
        make("T06", status="blocked"),
        make("T07", ("T06", "T05", "T04")),
    ]
    with pytest.raises(TransitionError) as exc:
        check_transition(plan[3], "running", plan)
    assert str(exc.value) == "T07 cannot start: waits for T04, T06"


def test_running_from_blocked_also_waits_for_dependencies() -> None:
    plan = [make("T01", status="ready"), make("T02", ("T01",), status="blocked")]
    with pytest.raises(TransitionError, match="T02 cannot start: waits for T01"):
        check_transition(plan[1], "running", plan)


def test_running_needs_a_valid_plan() -> None:
    plan = [make("T01", ("T02",)), make("T02", ("T01",))]
    with pytest.raises(PlanError, match="cycle: T01 → T02 → T01"):
        check_transition(plan[0], "running", plan)


def copy_dashboard(projects_dir: Path) -> Path:
    shutil.copytree(FIXTURES / "dashboard", projects_dir / "dashboard")
    return projects_dir / "dashboard" / "tickets"


def test_apply_transition_changes_only_the_status_line(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    path = tickets / "T01-repository-and-tooling.md"
    before = path.read_bytes()

    result = apply_transition("dashboard", "T01", "running", projects_dir=projects_dir)

    assert result.changed and result.previous == "ready"
    assert result.ticket.meta.status == "running"
    after = path.read_bytes()
    assert after == before.replace(b"status: ready\n", b"status: running\n")
    assert after != before
    assert load_ticket("dashboard", "T01", projects_dir=projects_dir).meta.status == "running"


def test_apply_same_status_writes_nothing(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    path = tickets / "T01-repository-and-tooling.md"
    mtime = path.stat().st_mtime_ns
    result = apply_transition("dashboard", "T01", "ready", projects_dir=projects_dir)
    assert not result.changed
    assert path.stat().st_mtime_ns == mtime


def test_apply_refused_leaves_the_file_alone(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    path = tickets / "T02-backend-scaffold.md"
    before = path.read_bytes()
    with pytest.raises(TransitionError, match="T02 cannot start: waits for T01"):
        apply_transition("dashboard", "T02", "running", projects_dir=projects_dir)
    with pytest.raises(TransitionError, match="ready → done is not allowed"):
        apply_transition("dashboard", "T02", "done", projects_dir=projects_dir)
    with pytest.raises(TransitionError, match="unknown status"):
        apply_transition("dashboard", "T02", "finished", projects_dir=projects_dir)
    assert path.read_bytes() == before


def test_apply_running_is_refused_while_a_file_is_invalid(projects_dir: Path) -> None:
    tickets = copy_dashboard(projects_dir)
    (tickets / "T99-broken.md").write_text("no frontmatter\n", encoding="utf-8")
    with pytest.raises(TransitionError, match=r"invalid \(tickets/T99-broken.md\)"):
        apply_transition("dashboard", "T01", "running", projects_dir=projects_dir)
    # Other moves do not look at the plan.
    apply_transition("dashboard", "T01", "draft", projects_dir=projects_dir)


def test_apply_unknown_ticket(projects_dir: Path) -> None:
    copy_dashboard(projects_dir)
    with pytest.raises(TicketError, match="no ticket T42"):
        apply_transition("dashboard", "T42", "ready", projects_dir=projects_dir)


# Scheduling ---------------------------------------------------------------------------


def test_next_ready_on_the_dashboard_plan() -> None:
    assert next_ready(dashboard()).id == "T01"  # type: ignore[union-attr]
    assert next_ready(dashboard(done=("T01",))).id == "T02"  # type: ignore[union-attr]
    assert next_ready(dashboard(done=("T01", "T02", "T05"))).id == "T03"  # type: ignore[union-attr]


def test_next_ready_skips_tickets_that_are_not_ready() -> None:
    plan = [make("T01", status="done"), make("T02", status="draft"), make("T03", ("T01",))]
    assert next_ready(plan).id == "T03"  # type: ignore[union-attr]
    assert next_ready([]) is None


def test_waiting_on() -> None:
    plan = dashboard(done=("T05",))
    t07 = next(t for t in plan if t.id == "T07")
    assert waiting_on(t07, plan) == ["T04", "T06"]
    # A ticket outside the list is checked against it.
    assert waiting_on(make("T19", ("T05", "T18")), plan) == ["T18"]


def test_scheduling_refuses_an_invalid_plan() -> None:
    plan = [make("T01", ("T02",)), make("T02", ("T01",)), make("T03", ("T99",))]
    for call in (next_ready, explain_idle, remaining_hours, critical_path, summary):
        with pytest.raises(PlanError) as exc:
            call(plan)
        assert messages(exc.value.problems) == [
            "T03 depends on T99, which does not exist",
            "cycle: T01 → T02 → T01",
        ]
        assert str(exc.value) == (
            "the plan has problems:\n"
            "  T03 depends on T99, which does not exist\n"
            "  cycle: T01 → T02 → T01"
        )
    with pytest.raises(PlanError):
        waiting_on(plan[0], plan)


def test_idle_none_when_a_ticket_is_ready() -> None:
    assert explain_idle(dashboard()) is None


def test_idle_all_done() -> None:
    reason = explain_idle(dashboard(done=tuple(t.id for t in dashboard())))
    assert reason is not None
    assert (reason.code, reason.ticket_ids, reason.message) == (
        "all_done",
        (),
        "all tickets are done",
    )


def test_idle_plan_not_approved() -> None:
    plan = [make("T01", status="done"), make("T02", status="draft"), make("T03", status="draft")]
    reason = explain_idle(plan)
    assert reason is not None
    assert reason.code == "plan_not_approved"
    assert reason.ticket_ids == ("T02", "T03")
    assert reason.message == "the plan is not approved yet: T02, T03 still in draft"


def test_idle_blocked() -> None:
    plan = [make("T01", status="blocked"), make("T02", ("T01",)), make("T03", status="blocked")]
    reason = explain_idle(plan)
    assert reason is not None
    assert (reason.code, reason.ticket_ids) == ("blocked", ("T01", "T03"))
    assert reason.message == "T01, T03 are blocked"


def test_idle_awaiting_approval() -> None:
    plan = [make("T01", status="awaiting_approval"), make("T02", ("T01",))]
    reason = explain_idle(plan)
    assert reason is not None
    assert (reason.code, reason.ticket_ids) == ("awaiting_approval", ("T01",))
    assert reason.message == "waiting for approval of T01"


def test_idle_running() -> None:
    plan = [make("T01", status="running"), make("T02", ("T01",)), make("T03", status="blocked")]
    reason = explain_idle(plan)
    assert reason is not None
    assert (reason.code, reason.ticket_ids) == ("running", ("T01",))
    assert reason.message == "T01 is running"
    two = [make("T01", status="running"), make("T02", status="running")]
    assert explain_idle(two).message == "T01, T02 are running"  # type: ignore[union-attr]


def test_idle_waiting() -> None:
    plan = [
        make("T01", status="draft"),
        make("T02", status="done"),
        make("T03", ("T01", "T02")),
        make("T04", ("T03",)),
    ]
    reason = explain_idle(plan)
    assert reason is not None
    assert (reason.code, reason.ticket_ids) == ("waiting", ("T03", "T04"))
    assert reason.waits_for == {"T03": ("T01",), "T04": ("T03",)}
    assert reason.message == "T03 waits for T01; T04 waits for T03"


# Progress figures ---------------------------------------------------------------------

DASHBOARD_PATH = ("T01", "T02", "T04", "T07", "T08", "T11", "T12", "T15", "T16", "T17", "T18")


def test_dashboard_remaining_hours() -> None:
    assert remaining_hours(dashboard()) == 38.5
    assert remaining_hours(dashboard(done=("T01", "T03"))) == 36


def test_dashboard_critical_path() -> None:
    path = critical_path(dashboard())
    assert path.ticket_ids == DASHBOARD_PATH  # T04 wins the tie with T06
    assert path.hours == 23.0


def test_critical_path_skips_done_tickets() -> None:
    path = critical_path(dashboard(done=("T01", "T02", "T04")))
    assert path.ticket_ids == ("T06", *DASHBOARD_PATH[3:])
    assert path.hours == 21.0


def test_critical_path_ties_prefer_lower_ids() -> None:
    # Two separate chains of 3h: T02 → T05 and T03 → T04; T01 alone is 1h.
    plan = [
        make("T01"),
        make("T05", ("T02",), estimate=2),
        make("T04", ("T03",), estimate=1.5),
        make("T03", estimate=1.5),
        make("T02"),
    ]
    assert critical_path(plan).ticket_ids == ("T02", "T05")
    # Decimal sums: 0.1 + 0.2 ties with 0.3 exactly.
    decimals = [
        make("T01", estimate=0.3),
        make("T02", estimate=0.1),
        make("T03", ("T02",), estimate=0.2),
    ]
    path = critical_path(decimals)
    assert (path.ticket_ids, path.hours) == (("T01",), 0.3)


def test_critical_path_when_everything_is_done() -> None:
    path = critical_path([make("T01", status="done")])
    assert (path.ticket_ids, path.hours) == ((), 0.0)
    assert remaining_hours([]) == 0


def test_dashboard_summary() -> None:
    figures = summary(dashboard(done=("T01", "T02")))
    assert dict(figures.counts) == {
        "draft": 0,
        "ready": 16,
        "running": 0,
        "awaiting_approval": 0,
        "blocked": 0,
        "done": 2,
    }
    assert list(figures.counts) == list(TICKET_STATUSES)
    assert figures.remaining_hours == 36.5
    assert figures.critical_path.ticket_ids == DASHBOARD_PATH[2:]
    assert figures.critical_path.hours == 21.0
