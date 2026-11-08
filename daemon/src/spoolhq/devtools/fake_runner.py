"""The fake runner's development scenarios: recorded transcripts in ``scenarios/``.

Implementer transcripts write ``backend/tests/test_spoolhq_fake.py`` (the built-in
template's layout) through ``FakeRunner``'s worktree check, so the project's real gates
run on a real change: the failing version fails the test gate. Reviewer transcripts get
their verdict's items from the prompt's "Done when" list, so they fit any ticket. The
planner always returns the same three-ticket plan.
"""

import json
import re
from pathlib import Path

from spoolhq.services.agents import FakeRunner
from spoolhq.services.runloop import Agents

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
DELAY_S = 0.5
"""Between transcript messages, so the Run tab plays the run live."""

SCENARIOS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    # name: (implementer transcripts, reviewer transcripts), each replayed in turn.
    "happy": (("implement.jsonl",), ("review-approve.jsonl",)),
    "gate-retry": (("implement-failing.jsonl", "implement.jsonl"), ("review-approve.jsonl",)),
    "review-changes": (
        ("implement.jsonl", "implement-again.jsonl"),
        ("review-changes.jsonl", "review-approve.jsonl"),
    ),
    "blocked": (("implement-failing.jsonl",), ("review-approve.jsonl",)),
    "plan": (("implement.jsonl",), ("review-approve.jsonl",)),
}

_DONE_WHEN = re.compile(r"<done_when>(.*?)</done_when>", re.DOTALL)
_ITEM = re.compile(r"^(\d+)\. .*$", re.MULTILINE)
_GATE_CHECKED = "(checked by the gates:"


def fill_verdict(prompt: str, transcript: str) -> str:
    """Puts one verdict item per "Done when" item of ``prompt`` into ``transcript``'s
    ``@@ITEMS@@``. All are met, except that a ``changes_requested`` verdict leaves the
    first item the gates don't check unmet (or the first item if they check all)."""
    block = _DONE_WHEN.search(prompt)
    items = list(_ITEM.finditer(block.group(1))) if block else []
    unmet = None
    if "changes_requested" in transcript and items:
        unmet = next((n for n, item in enumerate(items) if _GATE_CHECKED not in item[0]), 0)
    verdict = [
        {
            "index": int(item[1]),
            "met": n != unmet,
            "reason": "the fake runner wants one more test" if n == unmet else "looks done",
        }
        for n, item in enumerate(items)
    ]
    # The items sit inside a JSON string in the transcript, so they are escaped once more.
    return transcript.replace("@@ITEMS@@", json.dumps(json.dumps(verdict))[1:-1])


def dev_agents(scenario: str, *, delay_s: float = DELAY_S) -> Agents:
    """Fake runners for every role with ``scenario``'s transcripts; KeyError if unknown."""
    implementer, reviewer = SCENARIOS[scenario]

    def runner(names: tuple[str, ...], *, review: bool = False) -> FakeRunner:
        return FakeRunner(
            [SCENARIOS_DIR / name for name in names],
            delay_s=delay_s,
            cycle=True,
            render=fill_verdict if review else None,
        )

    return Agents(
        implementer=runner(implementer),
        reviewer=runner(reviewer, review=True),
        planner=runner(("plan.jsonl",)),
    )
