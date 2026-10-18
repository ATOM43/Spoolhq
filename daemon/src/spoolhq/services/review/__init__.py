"""Review: a second, independent agent checks a ticket's diff against its "Done when" list.

``review()`` runs a fresh, read-only agent (Read, Glob, Grep) in the worktree with the
ticket, the gate results and the diff, and returns a validated ``ReviewResult``. It
never sees the implementer's transcript, summary or progress note. This package
imports only ``services.agents`` and ``services.context``. See ``docs/review.md``.
"""

from spoolhq.services.review.diff import DIFF_MAX_CHARS, trim_diff
from spoolhq.services.review.model import (
    VERDICTS,
    GateLine,
    ItemVerdict,
    ReviewInputs,
    ReviewResult,
    Verdict,
)
from spoolhq.services.review.reviewer import (
    DEFAULT_BUDGET,
    REVIEWER_TEMPLATE,
    render_review_prompt,
    review,
)
from spoolhq.services.review.verdict import InvalidVerdict, ParsedVerdict, parse_verdict

__all__ = [
    "DEFAULT_BUDGET",
    "DIFF_MAX_CHARS",
    "REVIEWER_TEMPLATE",
    "VERDICTS",
    "GateLine",
    "InvalidVerdict",
    "ItemVerdict",
    "ParsedVerdict",
    "ReviewInputs",
    "ReviewResult",
    "Verdict",
    "parse_verdict",
    "render_review_prompt",
    "review",
    "trim_diff",
]
