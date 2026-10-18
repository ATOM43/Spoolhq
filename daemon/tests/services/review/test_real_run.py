"""One real review through the installed ``claude`` CLI (opt-in, uses a real model).

Same skip rule as ``tests/services/agents/test_real_run.py``: ``SPOOLHQ_REAL_AGENT=1``
and a logged-in ``claude``. With ``SPOOLHQ_RECORD=1`` the raw stream of the last
attempt is saved, anonymised, to ``tests/fixtures/review/recorded/real_review.jsonl``.
"""

import threading
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import ClaudeCliRunner, Outcome
from spoolhq.services.review import ReviewInputs, review
from spoolhq.services.tickets import read_ticket
from tests.conftest import REVIEW_FIXTURES, commit_file, run_git
from tests.services.agents.test_real_run import REAL, RECORD, anonymise, logged_in

RECORDING = REVIEW_FIXTURES / "recorded" / "real_review.jsonl"
SLUGS = (REVIEW_FIXTURES / "seeded.diff").read_text(encoding="utf-8")
SLUGS = "".join(
    line[1:] + "\n"
    for line in SLUGS.splitlines()
    if line.startswith("+") and not line.startswith("+++")
)

pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in()), reason="needs SPOOLHQ_REAL_AGENT=1 and a logged-in claude"
    ),
]


def test_real_review_names_the_missing_test(git_repo: Path, home: Path) -> None:
    run_git(git_repo, "checkout", "--quiet", "-b", "feat/T07-parse-slug")
    commit_file(git_repo, "slugs.py", SLUGS, "T07: add parse_slug")
    ticket = read_ticket(REVIEW_FIXTURES / "T07-parse-slug.md")
    inputs = ReviewInputs(
        ticket_id=ticket.id,
        title=ticket.meta.title,
        body=ticket.body,
        done_when=tuple(item.text for item in ticket.done_when),
        gate_checked={},
        diff=run_git(git_repo, "diff", "main...HEAD"),
        gate_summary=(),
        worktree=git_repo,
    )
    raw: list[dict[str, Any]] = []

    def keep(message: dict[str, Any]) -> None:
        if message.get("type") == "system" and message.get("subtype") == "init":
            raw.clear()  # a retry starts a new run; keep the last one
        raw.append(message)

    result = review(inputs, ClaudeCliRunner(), home=home, on_raw=keep, cancel=threading.Event())

    if RECORD:
        replacements = [
            (str(git_repo.resolve()), "<worktree>"),
            (str(git_repo), "<worktree>"),
            (str(home.resolve()), "<spoolhq-home>"),
            (str(Path.home()), "<home>"),
        ]
        RECORDING.parent.mkdir(parents=True, exist_ok=True)
        RECORDING.write_text(
            "".join(anonymise(message, replacements) + "\n" for message in raw),
            encoding="utf-8",
        )

    print(f"verdict={result.verdict} attempts={result.attempts} items={result.items}")
    assert result.run_outcome is Outcome.COMPLETED, result.summary
    assert result.verdict in ("changes_requested", "needs_human"), result.summary
    by_index = {item.index: item for item in result.items}
    assert set(by_index) == {1, 2, 3}
    assert by_index[2].met is False
    assert run_git(git_repo, "status", "--porcelain") == ""  # nothing changed
