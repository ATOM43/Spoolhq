"""One real planner run through the installed ``claude`` CLI (opt-in, uses a real model).

Same skip rule as ``tests/services/agents/test_real_run.py``: ``SPOOLHQ_REAL_AGENT=1``
and a logged-in ``claude``. It prints the calls and tokens used.
"""

import threading
from pathlib import Path

import pytest

from spoolhq.core.tokens import weighted_tokens
from spoolhq.services.agents import ClaudeCliRunner, Outcome
from spoolhq.services.planner import generate_plan
from spoolhq.services.scheduler import validate_plan
from spoolhq.services.tickets import list_tickets
from tests.services.agents.test_real_run import REAL, logged_in

pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in()), reason="needs SPOOLHQ_REAL_AGENT=1 and a logged-in claude"
    ),
]

SPEC = """\
# wordcount

Build `wc-lite`, a small Python command-line tool that counts lines, words and characters
in one or more text files, like a simplified `wc`. With no file it reads standard input.
Each file gets one output line with its counts and name, followed by a total line when
more than one file is given.

Options: `-l`, `-w` and `-c` limit the output to lines, words or characters, and `--json`
prints the counts as JSON instead. A missing or unreadable file prints an error to
standard error, the other files are still counted, and the exit code is 1.

It is a Python 3.12 package managed with uv, with pytest tests, ruff for linting and a
justfile with `just lint` and `just test`. No third-party runtime dependencies.
"""


def test_real_plan_for_a_small_cli_tool_validates(
    workspace: Path, projects_dir: Path, home: Path
) -> None:
    (workspace / "CONTEXT.md").write_text(SPEC, encoding="utf-8")

    result = generate_plan(
        "demo", ClaudeCliRunner(), projects_dir=projects_dir, home=home, cancel=threading.Event()
    )

    weighted = weighted_tokens(result.input_tokens, result.output_tokens, result.cache_read_tokens)
    print(
        f"calls={result.attempts} input={result.input_tokens} output={result.output_tokens} "
        f"cache_reads={result.cache_read_tokens} weighted={weighted} error={result.error}"
    )
    assert result.outcome is Outcome.COMPLETED, result.error
    assert result.error is None
    listing = list_tickets("demo", projects_dir=projects_dir)
    assert listing.invalid == []
    assert validate_plan(listing.tickets) == []
    assert listing.tickets and all(t.meta.status == "draft" for t in listing.tickets)
    for ticket in listing.tickets:
        print(
            f"{ticket.id} {ticket.meta.estimate_h:g}h {ticket.meta.depends_on} {ticket.meta.title}"
        )
        assert ticket.done_when[-1].text == "`just test` passes"
