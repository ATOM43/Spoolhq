"""Reading the reviewer's ``<verdict>`` block: pure and deterministic.

The final message must end with one ``<verdict>{…JSON…}</verdict>`` block; the last one
is used. The JSON is validated with Pydantic and then checked for consistency, so a
reviewer talked into ``approve`` with an unmet item still fails validation.
"""

import json
import re
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from spoolhq.services.review.model import Verdict

REASON_MAX = 1000
SUMMARY_MAX = 2000

_BLOCK_RE = re.compile(r"<verdict>(.*?)</verdict>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"\A```[A-Za-z]*\n(.*)\n```\Z", re.DOTALL)


class InvalidVerdict(ValueError):
    """The reviewer's output can't be used; ``errors`` says why, one line each."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


class ParsedItem(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    index: int
    met: bool
    reason: str = Field(min_length=1, max_length=REASON_MAX, pattern=r"\S")


class ParsedVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    items: tuple[ParsedItem, ...]
    verdict: Verdict
    summary: str = Field(max_length=SUMMARY_MAX)


def _location(loc: tuple[int | str, ...]) -> str:
    return ".".join(str(part) for part in loc) or "verdict"


def consistency_errors(verdict: str, met: Mapping[int, bool]) -> list[str]:
    """``approve`` needs every item met, ``changes_requested`` at least one not met."""
    unmet = sorted(index for index, ok in met.items() if not ok)
    if verdict == "approve":
        return [f"verdict 'approve' but item {index} is not met" for index in unmet]
    if verdict == "changes_requested" and not unmet:
        return ["verdict 'changes_requested' but every item is met"]
    return []


def parse_verdict(
    final_text: str, n_items: int, *, gate_checked: Mapping[int, bool] | None = None
) -> ParsedVerdict:
    """The last ``<verdict>`` block in ``final_text``, validated for ``n_items`` items.

    ``gate_checked`` (item index → gate result) replaces the reviewer's ``met`` for those
    items before the consistency check. Raises InvalidVerdict listing every problem.
    """
    blocks = _BLOCK_RE.findall(final_text)
    if not blocks:
        raise InvalidVerdict(["no <verdict> block in the final message"])
    raw = blocks[-1].strip()
    fence = _FENCE_RE.match(raw)
    if fence:
        raw = fence[1].strip()
    try:
        json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InvalidVerdict([f"the <verdict> block is not valid JSON: {exc}"]) from None
    try:
        # From the JSON text: strict mode accepts JSON arrays as tuples only there.
        parsed = ParsedVerdict.model_validate_json(raw)
    except ValidationError as exc:
        raise InvalidVerdict(
            [f"{_location(err['loc'])}: {err['msg']}" for err in exc.errors()]
        ) from None

    errors: list[str] = []
    seen: set[int] = set()
    for item in parsed.items:
        if not 1 <= item.index <= n_items:
            errors.append(f"items: index {item.index} out of range (1–{n_items})")
        elif item.index in seen:
            errors.append(f"items: index {item.index} appears more than once")
        seen.add(item.index)
    errors += [f"items: index {i} missing" for i in range(1, n_items + 1) if i not in seen]
    if errors:
        raise InvalidVerdict(errors)
    met = {item.index: item.met for item in parsed.items}
    met.update(gate_checked or {})
    errors = consistency_errors(parsed.verdict, met)
    if errors:
        raise InvalidVerdict(errors)
    return parsed
