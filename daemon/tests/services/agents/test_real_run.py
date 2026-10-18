"""One real run through the installed ``claude`` CLI (opt-in, uses a real model).

Runs only with ``SPOOLHQ_REAL_AGENT=1`` and a logged-in ``claude``. With
``SPOOLHQ_RECORD=1`` the raw stream is saved, anonymised, to
``tests/fixtures/agents/claude/recorded/real_run.jsonl``. The variables are read at
import, before the autouse ``home`` fixture clears ``SPOOLHQ_*``.
"""

import getpass
import json
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    Budget,
    ClaudeCliRunner,
    Outcome,
    PermissionDenied,
)
from tests.conftest import AGENT_FIXTURES

REAL = os.environ.get("SPOOLHQ_REAL_AGENT") == "1"
RECORD = os.environ.get("SPOOLHQ_RECORD") == "1"
RECORDING = AGENT_FIXTURES / "recorded" / "real_run.jsonl"
MODEL_RE = re.compile(r"claude-[a-z]+-[0-9][0-9a-z.-]*")
PROMPT = (
    "Create a file named hello.txt in the current directory containing exactly "
    "`hello from spoolhq` (no other text). Then try to run this shell command with the "
    "Bash tool: python3 -c 'print(1)'. If it is denied, do not retry it; just report "
    "what happened."
)


def logged_in() -> bool:
    claude = shutil.which("claude")
    if claude is None:
        return False
    try:
        status = subprocess.run(  # noqa: S603 - fixed argument list, no shell
            [claude, "auth", "status"], capture_output=True, timeout=15, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return status.returncode == 0


pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not (REAL and logged_in()), reason="needs SPOOLHQ_REAL_AGENT=1 and a logged-in claude"
    ),
]


def anonymise(message: dict[str, Any], replacements: list[tuple[str, str]]) -> str:
    text = json.dumps(message, ensure_ascii=False)
    for value, placeholder in replacements:
        text = text.replace(json.dumps(value)[1:-1], placeholder)
    text = re.sub(r'"session_id": "[^"]*"', '"session_id": "<session>"', text)
    text = MODEL_RE.sub("<model>", text)
    user = re.escape(getpass.getuser())
    return re.sub(rf"(?<![A-Za-z0-9_-]){user}(?![A-Za-z0-9_-])", "<user>", text)


def test_real_run_creates_a_file_and_is_denied_python(git_repo: Path, home: Path) -> None:
    policy = AgentPolicy.for_worktree(git_repo, {"test": "true"}, home)
    events: list[AgentEvent] = []
    raw: list[dict[str, Any]] = []
    result = ClaudeCliRunner().run(
        PROMPT,
        policy,
        Budget(max_turns=10, max_usd=None, max_tokens=None, timeout_s=600),
        on_event=events.append,
        on_raw=raw.append,
        cancel=threading.Event(),
    )

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

    assert result.outcome is Outcome.COMPLETED, result.error
    content = (git_repo / "hello.txt").read_text(encoding="utf-8")
    assert content.removesuffix("\n") == "hello from spoolhq"
    assert result.files_changed == ("hello.txt",)
    # Claude Code's env-scrub stubs (.env, package.json, ...) were cleaned up.
    assert sorted(path.name for path in git_repo.iterdir()) == [".git", "hello.txt"]
    denied = [event for event in events if isinstance(event, PermissionDenied)]
    assert len(denied) == 1, denied
    assert denied[0].tool == "Bash"
    assert "python3" in denied[0].input_summary
    assert result.input_tokens > 0
    assert result.output_tokens > 0
