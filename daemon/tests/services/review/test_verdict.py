import json
from typing import Any

import pytest

from spoolhq.services.review import InvalidVerdict, parse_verdict


def block(data: Any) -> str:
    return f"Done.\n<verdict>{json.dumps(data)}</verdict>"


def body(items: list[tuple[int, bool, str]], verdict: str = "approve") -> dict[str, Any]:
    return {
        "items": [{"index": i, "met": m, "reason": r} for i, m, r in items],
        "verdict": verdict,
        "summary": "ok",
    }


ALL_MET = [(1, True, "a"), (2, True, "b"), (3, True, "c")]


def errors(text: str, n: int = 3) -> list[str]:
    with pytest.raises(InvalidVerdict) as exc:
        parse_verdict(text, n)
    return exc.value.errors


def test_valid_verdict_parses() -> None:
    parsed = parse_verdict(block(body(ALL_MET)), 3)
    assert parsed.verdict == "approve"
    assert [item.index for item in parsed.items] == [1, 2, 3]


def test_items_in_any_order() -> None:
    assert parse_verdict(block(body(ALL_MET[::-1])), 3).verdict == "approve"


def test_missing_index() -> None:
    assert errors(block(body(ALL_MET[:1] + ALL_MET[2:]))) == ["items: index 2 missing"]


def test_duplicate_index() -> None:
    items = [(1, True, "a"), (2, True, "b"), (2, True, "b")]
    assert errors(block(body(items))) == [
        "items: index 2 appears more than once",
        "items: index 3 missing",
    ]


def test_out_of_range_index() -> None:
    items = [*ALL_MET, (4, True, "d")]
    assert errors(block(body(items))) == ["items: index 4 out of range (1–3)"]


@pytest.mark.parametrize("reason", ["", "   "])
def test_empty_reason(reason: str) -> None:
    [error] = errors(block(body([(1, True, reason), *ALL_MET[1:]])))
    assert error.startswith("items.0.reason: ")


def test_reason_too_long() -> None:
    [error] = errors(block(body([(1, True, "x" * 1001), *ALL_MET[1:]])))
    assert error.startswith("items.0.reason: String should have at most 1000 characters")


def test_unknown_key() -> None:
    data = body(ALL_MET)
    data["score"] = 9
    assert errors(block(data)) == ["score: Extra inputs are not permitted"]


def test_unknown_verdict_and_wrong_type() -> None:
    data = body(ALL_MET, verdict="lgtm")
    data["items"][0]["met"] = "yes"
    found = errors(block(data))
    assert any(error.startswith("items.0.met: ") for error in found)
    assert any(error.startswith("verdict: ") for error in found)


def test_approve_with_an_unmet_item() -> None:
    items = [(1, True, "a"), (2, False, "no test"), (3, True, "c")]
    assert errors(block(body(items, "approve"))) == ["verdict 'approve' but item 2 is not met"]


def test_changes_requested_with_everything_met() -> None:
    assert errors(block(body(ALL_MET, "changes_requested"))) == [
        "verdict 'changes_requested' but every item is met"
    ]


def test_needs_human_allowed_either_way() -> None:
    assert parse_verdict(block(body(ALL_MET, "needs_human")), 3).verdict == "needs_human"


def test_last_block_is_used() -> None:
    first = block(body(ALL_MET, "needs_human"))
    assert parse_verdict(first + "\n" + block(body(ALL_MET)), 3).verdict == "approve"


def test_json_in_a_code_fence_inside_the_block() -> None:
    text = f"<VERDICT>\n```json\n{json.dumps(body(ALL_MET))}\n```\n</Verdict>"
    assert parse_verdict(text, 3).verdict == "approve"


def test_no_block() -> None:
    assert errors("Looks good to me.") == ["no <verdict> block in the final message"]


def test_malformed_json() -> None:
    [error] = errors("<verdict>{'items': }</verdict>")
    assert error.startswith("the <verdict> block is not valid JSON: ")


def test_gate_checked_items_replace_the_reviewers_answer() -> None:
    items = [(1, True, "a"), (2, True, "b"), (3, False, "can't run it")]
    text = block(body(items, "approve"))
    assert parse_verdict(text, 3, gate_checked={3: True}).verdict == "approve"
    with pytest.raises(InvalidVerdict) as exc:
        parse_verdict(block(body(items, "changes_requested")), 3, gate_checked={3: True})
    assert exc.value.errors == ["verdict 'changes_requested' but every item is met"]
