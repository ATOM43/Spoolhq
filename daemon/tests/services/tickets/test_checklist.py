"""The "Done when" items the reviewer gets, from `parse_done_when`."""

from spoolhq.services.tickets import parse_done_when


def texts(body: str) -> tuple[str, ...]:
    return tuple(item.text for item in parse_done_when(body)[0])


def test_open_and_checked_items_keep_their_text() -> None:
    body = "## Done when\n- [ ] `parse_slug` exists in `slugs.py`\n- [x] `just test` passes\n"
    assert texts(body) == ("`parse_slug` exists in `slugs.py`", "`just test` passes")
    assert [item.checked for item in parse_done_when(body)[0]] == [False, True]


def test_no_heading_gives_no_items() -> None:
    assert texts("## Scope\n- [ ] not an item\n") == ()


def test_the_section_ends_at_the_next_heading() -> None:
    body = "## Done when\n- [ ] one\n\n## Notes\n- [ ] not an item\n"
    assert texts(body) == ("one",)
