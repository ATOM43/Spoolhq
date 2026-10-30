"""The merge policy: whether an approved ticket can land by itself or needs a person.

Plain values in, a ``PolicyDecision`` out; no git, no I/O. Every rule is evaluated and
every one that holds is recorded. ``delivery_mode`` turns a decision into how the work
lands. Computing the inputs (the squash diff's files) is ``services/git/diffstat.py``;
the wiring is ``Delivery`` (``delivery.py``). See ``docs/merge-policy.md``.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

from spoolhq.services.git import ChangedFile
from spoolhq.services.projects import LOCKFILES

DeliveryMode = Literal["direct", "pr", "approval"]
LISTED_PATHS = 10
SUMMARY_CHARS = 200


@dataclass(frozen=True)
class RuleHit:
    rule: str
    """``review_required``, ``diff_size``, ``protected_paths``, ``needs_human`` or
    ``hold_mode``."""
    detail: str


@dataclass(frozen=True)
class PolicyDecision:
    needs_human: bool
    rules: tuple[RuleHit, ...]


@lru_cache(maxsize=256)
def _compile(pattern: str) -> re.Pattern[str]:
    parts = pattern.split("/")
    regex = ""
    for index, part in enumerate(parts):
        last = index == len(parts) - 1
        if part == "**":
            regex += ".*" if last else "(?:[^/]+/)*"
            continue
        for char in part:
            regex += "[^/]*" if char == "*" else "[^/]" if char == "?" else re.escape(char)
        regex += "" if last else "/"
    return re.compile(regex)


def path_matches(pattern: str, path: str) -> bool:
    """Whether the repo-relative POSIX ``path`` matches ``pattern``, case-sensitively:
    ``*`` and ``?`` stay within one folder, ``**`` spans any number of folders (none
    too). Platform-independent, unlike ``fnmatch``."""
    return _compile(pattern).fullmatch(path) is not None


def _listed(paths: Sequence[str]) -> str:
    text = ", ".join(paths[:LISTED_PATHS])
    more = len(paths) - LISTED_PATHS
    return text + (f" and {more} more" if more > 0 else "")


def evaluate(
    *,
    review_required: bool,
    changes: Sequence[ChangedFile],
    max_diff_lines: int,
    protected: Sequence[str],
    reviewer_summary: str | None,
    hold: bool = False,
) -> PolicyDecision:
    """Apply every rule. ``reviewer_summary`` is set when the reviewer said
    ``needs_human`` (listed first, so a person reads it first); ``hold`` is
    ``run.integration: hold``."""
    hits: list[RuleHit] = []
    if reviewer_summary is not None:
        summary = " ".join(reviewer_summary.split())[:SUMMARY_CHARS]
        hits.append(RuleHit("needs_human", summary or "the reviewer asked for a person"))
    if review_required:
        hits.append(RuleHit("review_required", "the ticket is marked review_required"))
    lines = sum(
        change.added + change.removed
        for change in changes
        if change.path.rsplit("/", 1)[-1] not in LOCKFILES
    )
    if lines > max_diff_lines:
        hits.append(RuleHit("diff_size", f"{lines} lines > {max_diff_lines}"))
    names = [name for change in changes for name in (change.old_path, change.path) if name]
    matched = [
        name
        for name in dict.fromkeys(names)
        if any(path_matches(pattern, name) for pattern in protected)
    ]
    if matched:
        hits.append(RuleHit("protected_paths", _listed(matched)))
    if hold:
        hits.append(RuleHit("hold_mode", "run.integration is hold"))
    return PolicyDecision(needs_human=bool(hits), rules=tuple(hits))


def delivery_mode(decision: PolicyDecision, has_remote: bool) -> DeliveryMode:
    """``direct`` when no rule holds. Otherwise a person decides: in a pull request with
    a GitHub remote, else (and always for ``hold_mode``) by local approval."""
    if not decision.needs_human:
        return "direct"
    if has_remote and all(hit.rule != "hold_mode" for hit in decision.rules):
        return "pr"
    return "approval"


def describe(rules: Sequence[RuleHit] | Sequence[dict[str, Any]]) -> str:
    """``needs you: diff_size (812 lines > 400), protected_paths (.github/ci.yml)``, or
    ``""`` when no rule holds."""
    pairs = [
        (hit.rule, hit.detail) if isinstance(hit, RuleHit) else (hit["rule"], hit["detail"])
        for hit in rules
    ]
    if not pairs:
        return ""
    return "needs you: " + ", ".join(f"{rule} ({detail})" for rule, detail in pairs)


def as_record(decision: PolicyDecision, mode: DeliveryMode, **extra: Any) -> dict[str, Any]:
    """The decision as stored on the run and in its ``policy.decision`` event."""
    rules = [{"rule": hit.rule, "detail": hit.detail} for hit in decision.rules]
    return {"mode": mode, "rules": rules, **extra}
