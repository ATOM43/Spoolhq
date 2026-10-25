import json
from typing import Any

import pytest

from spoolhq.services.planner import Existing, InvalidPlan, check_plan, next_id, parse_plan
from spoolhq.services.tickets import parse_ticket
from tests.conftest import dashboard_plan


def block(data: Any) -> str:
    return f"Done.\n<plan>{json.dumps(data)}</plan>"


NONE = Existing((), ())


def errors(text: str, existing: Existing = NONE) -> list[str]:
    with pytest.raises(InvalidPlan) as info:
        check_plan(parse_plan(text), existing, "just test")
    return info.value.errors


def existing_ticket(ticket_id: str, status: str = "done", deps: str = "[]") -> Any:
    text = (
        f"---\nid: {ticket_id}\ntitle: Old\nphase: 0\ndepends_on: {deps}\nstatus: {status}\n"
        "estimate_h: 2\n---\n"
    )
    return parse_ticket(text, f"{ticket_id}-old.md")


def test_the_dashboard_plan_checks_out() -> None:
    checked = check_plan(parse_plan(block(dashboard_plan())), Existing((), ()), "just test")
    assert [t.id for t in checked.tickets] == [f"T{n:02d}" for n in range(1, 19)]
    assert list(checked.drafts)[0] == "T01-repository-and-tooling.md"


def test_the_last_block_wins_and_a_fence_inside_is_accepted() -> None:
    data = {"tickets": dashboard_plan()["tickets"][:1]}
    text = f"<plan>junk</plan>\n<PLAN>\n```json\n{json.dumps(data)}\n```\n</PLAN>"
    assert parse_plan(text).tickets[0].id == "T01"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no block", "no <plan> block in the final message"),
        (
            '<plan>{"tickets": []}</plan>',
            "tickets: Tuple should have at least 1 item after validation, not 0",
        ),
        ('<plan>{"tickets": [{"id": "T01"}]}</plan>', "T01: title: Field required"),
        ('<plan>{"tickets": [{"id": "bad\\nid"}]}</plan>', "tickets.0.title: Field required"),
        ("<plan>[]</plan>", "plan: Input should be an object"),
    ],
)
def test_parse_errors(text: str, message: str) -> None:
    with pytest.raises(InvalidPlan) as info:
        parse_plan(text)
    assert message in info.value.errors


def test_a_dependency_on_a_missing_ticket_is_reported() -> None:
    data = {"tickets": dashboard_plan()["tickets"][1:2]}  # T02 depends on T01
    assert errors(block(data)) == ["T02 depends on T01, which does not exist"]


def test_a_self_dependency_is_reported_by_the_ticket_store() -> None:
    data = {"tickets": dashboard_plan()["tickets"][:1]}
    data["tickets"][0]["depends_on"] = ["T01"]
    assert errors(block(data)) == [
        "tickets/T01-repository-and-tooling.md: depends_on: T01 cannot depend on itself"
    ]


def test_ids_of_kept_tickets_cannot_be_reused() -> None:
    kept = Existing((existing_ticket("T01"),), ())
    data = {"tickets": dashboard_plan()["tickets"][:1]}
    assert errors(block(data), kept) == ["T01: the id belongs to a kept ticket"]


def test_replaced_drafts_free_their_ids() -> None:
    replaceable = Existing((existing_ticket("T05"),), (existing_ticket("T01", "draft"),))
    data = {"tickets": dashboard_plan()["tickets"][:1]}
    assert check_plan(parse_plan(block(data)), replaceable, "just test").tickets[0].id == "T01"


def test_next_id_follows_every_existing_ticket() -> None:
    assert next_id(Existing((), ())) == "T01"
    assert next_id(Existing((existing_ticket("T99"),), (existing_ticket("T07", "draft"),))) == (
        "T100"
    )


def test_the_test_command_item_is_added_when_missing() -> None:
    data = {"tickets": dashboard_plan()["tickets"][:1]}
    data["tickets"][0]["done_when"] = ["CI is green"]
    [ticket] = check_plan(parse_plan(block(data)), Existing((), ()), "make check").tickets
    assert [item.text for item in ticket.done_when] == ["CI is green", "`make check` passes"]
