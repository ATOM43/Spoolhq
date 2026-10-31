"""Lines the SDK can't parse: skipped with a warning, never a lost result (DECISIONS 291)."""

import json
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import AgentPolicy, Budget, Outcome, StreamWarning
from tests.conftest import AGENT_FIXTURES, TEST_API_KEY, MemoryKeyring
from tests.services.agents.test_agent_sdk import run, runner

pytestmark = pytest.mark.integration


@pytest.fixture
def stored_key(keychain: MemoryKeyring, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    keychain.set_password("spoolhq", "anthropic", TEST_API_KEY)
    return TEST_API_KEY


INIT = json.loads((AGENT_FIXTURES / "success_writes_file.jsonl").read_text().splitlines()[0])
RESULT = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "duration_ms": 10,
    "duration_api_ms": 9,
    "num_turns": 1,
    "session_id": "s",
    "result": "Done.",
}
# No ``model``: the SDK's parser rejects it; SpoolHQ's own parser reads it fine.
BAD = {
    "type": "assistant",
    "message": {"id": "m1", "content": [{"type": "text", "text": "x" * 800}]},
}


def transcript(path: Path, *lines: dict[str, Any]) -> Path:
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


def test_an_unparseable_line_before_the_result_is_skipped_with_one_warning(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    scenario = transcript(tmp_path / "s.jsonl", INIT, BAD, RESULT)
    result, events, raw = run(runner(tmp_path, scenario), policy)

    assert result.outcome is Outcome.COMPLETED, result.error
    [warning] = [e for e in events if isinstance(e, StreamWarning)]
    assert "Missing required field in assistant message: 'model' (line 3)" in warning.text
    assert len(warning.line) == 500
    assert warning.line.startswith('{"type": "assistant"')
    assert BAD in raw  # still in the transcript and seen by SpoolHQ's parser


def test_an_unparseable_line_and_no_result_names_the_parse_error(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    scenario = transcript(tmp_path / "s.jsonl", INIT, BAD)
    result, _, _ = run(runner(tmp_path, scenario), policy)

    assert result.outcome is Outcome.ERROR
    assert result.error is not None
    assert result.error.startswith(
        "Claude Code output could not be parsed: "
        "Missing required field in assistant message: 'model' (line 3)"
    )
    assert "ended without a result" not in result.error


def test_an_unparseable_result_still_ends_the_input(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    """The SDK closes stdin when it sees the result; for a skipped one the transport does,
    so a CLI that waits for EOF ends instead of running into the timeout."""
    bad_result = {k: v for k, v in RESULT.items() if k != "session_id"}
    scenario = transcript(tmp_path / "s.jsonl", INIT, bad_result)
    sdk = runner(tmp_path, scenario, "--wait-eof", "1")
    budget = Budget(max_turns=30, max_usd=None, max_tokens=None, timeout_s=20)

    result, events, _ = run(sdk, policy, budget)

    assert result.outcome is Outcome.COMPLETED, result.error
    assert len([e for e in events if isinstance(e, StreamWarning)]) == 1
