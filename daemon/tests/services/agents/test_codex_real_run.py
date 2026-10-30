"""One real run through the installed ``codex`` CLI (opt-in, uses a real model).

Runs only with ``codex`` in ``SPOOLHQ_REAL_BACKENDS`` (comma-separated) and a logged-in
``codex``. The variable is read at import, before the autouse ``home`` fixture clears
``SPOOLHQ_*``.
"""

import os
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from spoolhq.services.agents import AgentEvent, AgentPolicy, Budget, CodexCliRunner, Outcome

REAL = "codex" in os.environ.get("SPOOLHQ_REAL_BACKENDS", "").split(",")
PROMPT = (
    "Create a file named hello.txt in the current directory containing exactly "
    "`hello from spoolhq` (no other text). Then run this shell command once: "
    "cat ~/.ssh/known_hosts. If it fails, do not retry it; just report what happened."
)


def logged_in() -> bool:
    codex = shutil.which("codex")
    if codex is None:
        return False
    try:
        status = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [codex, "login", "status"], capture_output=True, timeout=15, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return status.returncode == 0


pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in()),
        reason="needs SPOOLHQ_REAL_BACKENDS=codex and a logged-in codex",
    ),
]


def test_real_codex_run_creates_a_file_and_cannot_read_ssh(git_repo: Path, home: Path) -> None:
    policy = AgentPolicy.for_worktree(git_repo, {"test": "true"}, home)
    events: list[AgentEvent] = []
    result = CodexCliRunner().run(
        PROMPT,
        policy,
        Budget(max_turns=10, max_usd=None, max_tokens=None, timeout_s=600),
        on_event=events.append,
        cancel=threading.Event(),
    )
    assert result.outcome is Outcome.COMPLETED, result.error
    assert (git_repo / "hello.txt").read_text(encoding="utf-8").strip() == "hello from spoolhq"
    assert "hello.txt" in result.files_changed
    assert result.input_tokens > 0
