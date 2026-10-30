"""One real run of the loop with the installed ``claude`` for both roles (opt-in).

Runs only with ``SPOOLHQ_REAL_AGENT=1`` and a logged-in ``claude``: a scratch project
with one tiny ticket, real gates (this interpreter's pytest) and the test integrator.
Prints the outcome, the attempts and the tokens (run with ``-s`` to see them).
"""

import json
import sys
from pathlib import Path

import pytest

from spoolhq.services.projects import init_project, load_project, save_project
from spoolhq.services.runloop import RunLoop
from spoolhq.services.runs import RunRegistry, RunStatus, attempt_dir
from tests.services.agents.test_real_run import REAL, logged_in
from tests.services.runloop.conftest import Merging

pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in()), reason="needs SPOOLHQ_REAL_AGENT=1 and a logged-in claude"
    ),
]

PYTHON = Path(sys.executable).as_posix()
TEST_COMMAND = f"{PYTHON} -m pytest -q"
TICKET = f"""\
---
id: T01
title: Say hello
phase: 1
depends_on: []
status: ready
estimate_h: 0.5
---

## Scope
Add a function `hello()` to `hello.py` that returns the string `"hello"`, and a pytest
test for it in `test_hello.py`.

## Done when
- [ ] `hello.py` defines `hello()`, which returns `"hello"`
- [ ] `test_hello.py` has a test that calls `hello()`
- [ ] `{TEST_COMMAND}` passes
"""


def model_calls(attempt_dir: Path) -> int:
    """Distinct assistant message ids in an attempt's transcript (both roles)."""
    transcript = attempt_dir / "transcript.jsonl"
    if not transcript.is_file():
        return 0
    messages = [json.loads(line) for line in transcript.read_text(encoding="utf-8").splitlines()]
    return len({m["message"]["id"] for m in messages if m.get("type") == "assistant"})


def test_real_run_implements_and_approves_a_tiny_ticket(
    repo: Path, projects_dir: Path, tmp_path: Path, home: Path
) -> None:
    workspace = init_project("scratch", repo, projects_dir=projects_dir).path
    (workspace / "tickets").mkdir(exist_ok=True)
    (workspace / "tickets" / "T01-say-hello.md").write_text(TICKET, encoding="utf-8")
    settings = load_project("scratch", projects_dir=projects_dir)
    settings.commands.install = f"{PYTHON} --version"
    settings.commands.lint = f"{PYTHON} -m compileall -q ."
    settings.commands.test = TEST_COMMAND
    # Every role set explicitly; the loop builds the runners from project.yaml.
    for role in ("planner", "implementer", "reviewer"):
        setattr(settings.agents, role, "claude-code-cli")
    save_project(settings, projects_dir=projects_dir)
    registry = RunRegistry.start(projects_dir, daemon_instance="real")
    loop = RunLoop(
        registry,
        projects_dir=projects_dir,
        worktrees_dir=tmp_path / "worktrees",
        home=home,
        integrator=Merging(),
    )
    try:
        run = loop.start("scratch")
        loop.wait("scratch")
        log = registry.get("scratch").run_log
        final = log.get_run(run.id)
        attempts = log.list_attempts(run.id)
        usage = log.run_usage(run.id)
        lines = [line for _, line in loop.current("scratch").phases]
    finally:
        loop.close()
        registry.close()

    print("\n".join(lines))
    print(f"outcome: {final.status.value} ({final.reason})")
    print("attempts:", [(a.number, a.kind.value, a.status.value) for a in attempts])
    print(f"model calls: {sum(model_calls(attempt_dir(workspace, a)) for a in attempts)}")
    print(
        f"tokens: {usage.input_tokens:,} in ({usage.cache_read_tokens:,} cache reads), "
        f"{usage.output_tokens:,} out, {usage.weighted_tokens:,} weighted"
    )
    print(f"progress note: {final.progress_note}")
    assert final.status is RunStatus.DONE, final.reason
