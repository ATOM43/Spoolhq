"""One real run through the Claude Agent SDK backend (opt-in, uses a real model and an
API key, so it costs money).

Runs only with ``agent-sdk`` in ``SPOOLHQ_REAL_BACKENDS`` (comma-separated) and an
Anthropic API key in ``ANTHROPIC_API_KEY`` or the keychain (``spool secrets set
anthropic``); otherwise it is skipped and says why. Both are read at import, before the
autouse fixtures clear ``SPOOLHQ_*`` and swap the keychain for an in-memory one.
"""

import os
import threading
from decimal import Decimal
from pathlib import Path

import keyring
import pytest
from keyring.errors import KeyringError

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentSdkRunner,
    Budget,
    Outcome,
    PermissionDenied,
)

REAL = "agent-sdk" in os.environ.get("SPOOLHQ_REAL_BACKENDS", "").split(",")
PROMPT = (
    "Create a file named hello.txt in the current directory containing exactly "
    "`hello from spoolhq` (no other text). Then run this shell command once: "
    "cat ~/.ssh/known_hosts. If it is denied, do not retry it; just report what happened."
)


def real_key() -> str | None:
    if not REAL:
        return None  # never touch the keychain unless asked to
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    try:
        return (keyring.get_password("spoolhq", "anthropic") or "").strip() or None
    except (KeyringError, RuntimeError):
        return None


KEY = real_key()

pytestmark = [
    pytest.mark.real_agent,
    pytest.mark.integration,
    pytest.mark.skipif(
        not REAL, reason="opt-in: set SPOOLHQ_REAL_BACKENDS=agent-sdk (costs API credit)"
    ),
    pytest.mark.skipif(
        REAL and KEY is None,
        reason="no Anthropic API key: set ANTHROPIC_API_KEY or run spool secrets set anthropic",
    ),
]


def test_real_agent_sdk_run_creates_a_file_and_is_denied_ssh(
    git_repo: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert KEY is not None
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    policy = AgentPolicy.for_worktree(git_repo, {"test": "true"}, home)
    events: list[AgentEvent] = []
    result = AgentSdkRunner().run(
        PROMPT,
        policy,
        Budget(max_turns=10, max_usd=Decimal("0.50"), max_tokens=None, timeout_s=600),
        on_event=events.append,
        cancel=threading.Event(),
    )
    assert result.outcome is Outcome.COMPLETED, result.error
    assert (git_repo / "hello.txt").read_text(encoding="utf-8").strip() == "hello from spoolhq"
    assert result.files_changed == ("hello.txt",)
    assert result.cost_micro_usd is not None and result.cost_micro_usd > 0
    denied = [event for event in events if isinstance(event, PermissionDenied)]
    assert any("known_hosts" in event.input_summary for event in denied)
    assert KEY not in repr(events) + repr(result)
