"""The Claude Agent SDK backend: the policy hook, the API key, refusals and a run through
the real SDK client with the fake CLI (``fake_sdk_cli.py``)."""

import hashlib
import json
import logging
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any

import keyring
import pytest
from keyring.errors import KeyringError

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    AgentSdkRunner,
    BackendUnavailableError,
    Budget,
    Outcome,
    PermissionDenied,
    RunResult,
)
from spoolhq.services.agents.agent_sdk import (
    MISSING_KEY,
    api_key,
    store_api_key,
)
from tests.conftest import (
    AGENT_FIXTURES,
    AGENT_PROMPT,
    TEST_API_KEY,
    MemoryKeyring,
    fake_sdk_cmd,
    sandbox_which,
)

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None, timeout_s=60)
pytestmark = pytest.mark.integration  # each run starts the fake CLI as a subprocess


@pytest.fixture(autouse=True)
def no_parent_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.fixture
def stored_key(keychain: MemoryKeyring) -> str:
    keychain.set_password("spoolhq", "anthropic", TEST_API_KEY)
    return TEST_API_KEY


def runner(tmp_path: Path, scenario: Path, *options: str, **kwargs: Any) -> AgentSdkRunner:
    return AgentSdkRunner(
        cli_cmd=fake_sdk_cmd(scenario, tmp_path / "record.json", *options),
        platform=kwargs.pop("platform", "linux"),
        which=sandbox_which,
        home=tmp_path / "user-home",
        **kwargs,
    )


def run(
    sdk: AgentSdkRunner, policy: AgentPolicy, budget: Budget = BUDGET
) -> tuple[RunResult, list[AgentEvent], list[dict[str, Any]]]:
    events: list[AgentEvent] = []
    raw: list[dict[str, Any]] = []
    result = sdk.run(
        AGENT_PROMPT,
        policy,
        budget,
        on_event=events.append,
        on_raw=raw.append,
        cancel=threading.Event(),
    )
    return result, events, raw


def record(tmp_path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((tmp_path / "record.json").read_text(encoding="utf-8"))
    return data


def scenario(path: Path, *messages: dict[str, Any]) -> Path:
    """A transcript: an init, ``messages``, then a success result."""
    init = json.loads((AGENT_FIXTURES / "success_writes_file.jsonl").read_text().splitlines()[0])
    result = {"type": "result", "subtype": "success", "is_error": False, "num_turns": 1}
    result.update(total_cost_usd=0.0123, result="Done.")
    lines = [init, *messages, result]
    path.write_text("".join(json.dumps(line) + "\n" for line in lines), encoding="utf-8")
    return path


def tool_use(tool_id: str, name: str, tool_input: dict[str, Any]) -> list[dict[str, Any]]:
    """An assistant tool call and its (successful) recorded result."""
    call = {"type": "tool_use", "id": tool_id, "name": name, "input": tool_input}
    reply = {"type": "tool_result", "tool_use_id": tool_id, "content": "ok"}
    return [
        {"type": "assistant", "message": {"id": f"msg_{tool_id}", "model": "m", "content": [call]}},
        {"type": "user", "message": {"role": "user", "content": [reply]}},
    ]


# --- the key --------------------------------------------------------------------------


def test_the_key_comes_from_the_environment_then_the_keychain(
    monkeypatch: pytest.MonkeyPatch, keychain: MemoryKeyring
) -> None:
    assert api_key() is None
    store_api_key(f"  {TEST_API_KEY}\n")
    assert api_key() == (TEST_API_KEY, "keychain")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-from-env")
    assert api_key() == ("sk-ant-from-env", "environment")
    with pytest.raises(ValueError, match="empty"):
        store_api_key("  ")


def test_an_unreadable_keychain_means_no_key(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(service: str, key: str) -> str:
        raise KeyringError("locked")

    monkeypatch.setattr(keyring, "get_password", broken)
    assert api_key() is None


def test_without_a_key_nothing_starts(tmp_path: Path, policy: AgentPolicy) -> None:
    sdk = runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl")
    info = sdk.detect()
    assert (info.installed, info.logged_in, info.reason) == (True, False, MISSING_KEY)
    assert MISSING_KEY == (
        "backend 'claude-agent-sdk' needs an API key; run spool secrets set anthropic"
    )
    record_path = tmp_path / "record.json"
    record_path.unlink(missing_ok=True)  # detect's --version leaves none, but be sure
    with pytest.raises(BackendUnavailableError, match="^backend 'claude-agent-sdk' needs an API"):
        run(sdk, policy)
    assert not record_path.exists()


def test_a_stored_login_is_never_used(tmp_path: Path, policy: AgentPolicy, stored_key: str) -> None:
    # The CLI gets a fresh, empty config folder, never ~/.claude with its login.
    result, _, _ = run(runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl"), policy)
    assert result.outcome is Outcome.COMPLETED
    config_dir = record(tmp_path)["env"]["CLAUDE_CONFIG_DIR"]
    assert Path(config_dir).name.startswith("spoolhq-sdk-")
    assert not Path(config_dir).exists()  # removed after the run
    assert "--setting-sources=" in record(tmp_path)["argv"]

    # A CLI that still reports another credential (a claude.ai login) is stopped.
    claude_ai = runner(
        tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl", "--key-source", "none"
    )
    result, _, _ = run(claude_ai, policy)
    assert result.outcome is Outcome.ERROR
    assert result.error is not None
    assert result.error.startswith("policy not enforced: init reports key source 'none'")
    assert result.files_changed == ()


def test_the_key_stays_out_of_argv_logs_events_and_files(
    tmp_path: Path,
    policy: AgentPolicy,
    stored_key: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    denied = scenario(tmp_path / "denied.jsonl", *tool_use("t1", "Bash", {"command": "curl x"}))
    result, events, raw = run(runner(tmp_path, denied), policy)
    assert result.outcome is Outcome.COMPLETED
    seen = record(tmp_path)
    # The key reached the CLI's environment, and only there.
    assert seen["api_key_sha256"] == hashlib.sha256(stored_key.encode()).hexdigest()
    assert seen["env"]["CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"] == "1"  # not to the agent's commands
    assert stored_key not in json.dumps(seen)
    assert stored_key not in caplog.text
    assert stored_key not in repr(events) + repr(result) + json.dumps(raw)
    for path in tmp_path.rglob("*"):
        if path.is_file():
            assert stored_key.encode() not in path.read_bytes(), path


def test_the_parent_key_passes_only_through_the_lookup(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", TEST_API_KEY)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_secret")
    monkeypatch.setenv("SPOOLHQ_TOKEN", "spoolhq-secret")
    result, _, _ = run(runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl"), policy)
    assert result.outcome is Outcome.COMPLETED
    names = set(record(tmp_path)["env_names"])
    assert "ANTHROPIC_API_KEY" in names
    assert not names & {"GITHUB_TOKEN", "SPOOLHQ_TOKEN", "ANTHROPIC_AUTH_TOKEN"}


# --- runs -----------------------------------------------------------------------------


def test_a_denied_call_is_reported_with_the_hooks_reason_and_logged(
    tmp_path: Path, policy: AgentPolicy, stored_key: str, caplog: pytest.LogCaptureFixture
) -> None:
    calls = [
        *tool_use("t1", "Bash", {"command": "just test; curl x"}),
        *tool_use("t2", "Write", {"file_path": str(tmp_path / "outside.txt"), "content": "x"}),
        *tool_use("t3", "Read", {"file_path": "~/.ssh/id_ed25519"}),
        *tool_use("t4", "Bash", {"command": "just test"}),
    ]
    result, events, _ = run(runner(tmp_path, scenario(tmp_path / "s.jsonl", *calls)), policy)
    denied = [event for event in events if isinstance(event, PermissionDenied)]
    assert [event.tool for event in denied] == ["Bash", "Write", "Read"]
    assert "contains shell operators" in denied[0].reason
    assert "outside the worktree" in denied[1].reason
    assert "under ~/.ssh" in denied[2].reason
    assert result.denials == tuple(denied)
    assert not (tmp_path / "outside.txt").exists()
    hooks = record(tmp_path)["hooks"]
    assert [hook["output"] == {} for hook in hooks] == [False, False, False, True]
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len([w for w in warnings if w.startswith("agent permission denied")]) == 3


def test_the_command_line(tmp_path: Path, policy: AgentPolicy, stored_key: str) -> None:
    budget = Budget(max_turns=7, max_usd=None, max_tokens=None)
    sdk = runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl", model="claude-x")
    run(sdk, policy, budget)
    argv = record(tmp_path)["argv"]
    assert argv[argv.index("--max-turns") + 1] == "7"
    assert argv[argv.index("--model") + 1] == "claude-x"
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert argv[argv.index("--input-format") + 1] == "stream-json"
    assert "--restricted" in argv and "--bare" not in argv  # bare drops SDK hooks and tools
    assert "--max-budget-usd" not in argv
    assert AGENT_PROMPT not in " ".join(argv)
    assert AGENT_PROMPT in record(tmp_path)["stdin"]
    settings = json.loads(argv[argv.index("--settings") + 1])
    assert settings["sandbox"]["failIfUnavailable"] is True


def test_a_read_only_run_gets_only_the_read_tools(
    tmp_path: Path, worktree: Path, home: Path, stored_key: str
) -> None:
    review = tmp_path / "review.jsonl"
    lines = (AGENT_FIXTURES / "success_writes_file.jsonl").read_text().splitlines()
    init = json.loads(lines[0]) | {"tools": ["Read", "Glob", "Grep"]}
    review.write_text(json.dumps(init) + "\n" + lines[-1] + "\n", encoding="utf-8")
    policy = AgentPolicy.read_only_for(worktree, home, role="planner")
    result, _, _ = run(runner(tmp_path, review), policy)
    assert result.outcome is Outcome.COMPLETED
    argv = record(tmp_path)["argv"]
    assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"
    assert not [arg for arg in argv if arg.startswith(("Bash(", "Write", "Edit"))]


def test_cost_is_recorded_and_the_budget_is_passed_on(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    budget = Budget(max_turns=30, max_usd=Decimal("0.50"), max_tokens=None)
    result, _, _ = run(
        runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl"), policy, budget
    )
    assert result.cost_micro_usd == 12_300
    argv = record(tmp_path)["argv"]
    assert argv[argv.index("--max-budget-usd") + 1] == "0.50"

    # The CLI stops the run when the budget is spent.
    over = tmp_path / "over.jsonl"
    lines = (AGENT_FIXTURES / "success_writes_file.jsonl").read_text().splitlines()
    end = json.loads(lines[-1]) | {"subtype": "error_max_budget_usd", "is_error": True}
    over.write_text("\n".join([*lines[:-1], json.dumps(end)]) + "\n", encoding="utf-8")
    result, _, _ = run(runner(tmp_path, over), policy, budget)
    assert result.outcome is Outcome.BUDGET_EXHAUSTED


@pytest.mark.parametrize(
    "error",
    ["Your credit balance is too low", "You have reached your specified API usage limits"],
)
def test_a_billing_or_quota_error_blocks(
    tmp_path: Path, policy: AgentPolicy, stored_key: str, error: str
) -> None:
    path = tmp_path / "billing.jsonl"
    lines = (AGENT_FIXTURES / "success_writes_file.jsonl").read_text().splitlines()
    end = {"type": "result", "subtype": "success", "is_error": True, "result": error}
    path.write_text(lines[0] + "\n" + json.dumps(end) + "\n", encoding="utf-8")
    result, _, _ = run(runner(tmp_path, path), policy)
    assert (result.outcome, result.reset_at) == (Outcome.ERROR, None)
    assert result.error is not None and "add credit or raise the limit" in result.error


def test_a_failed_cli_reports_its_stderr(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")
    sdk = runner(tmp_path, empty, "--exit-code", "2", "--stderr", "boom from the cli")
    result, _, _ = run(sdk, policy)
    assert result.outcome is Outcome.ERROR
    assert result.error is not None and "boom from the cli" in result.error


def test_a_local_endpoint_gets_the_dummy_token_not_the_key(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    sdk = runner(
        tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl", base_url="http://localhost:11434"
    )
    assert sdk.detect().auth_method == "endpoint token"
    result, _, _ = run(sdk, policy)
    assert result.outcome is Outcome.COMPLETED
    seen = record(tmp_path)
    assert seen["env"]["ANTHROPIC_BASE_URL"] == "http://localhost:11434"
    assert seen["env"]["ANTHROPIC_AUTH_TOKEN"] == "spoolhq-local-endpoint"  # noqa: S105
    assert seen["api_key_sha256"] is None


def test_a_remote_endpoint_needs_its_own_token(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    sdk = runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl", base_url="https://x.io")
    with pytest.raises(BackendUnavailableError, match="needs its own token"):
        run(sdk, policy)


def test_detect_refuses_what_it_cannot_enforce(tmp_path: Path, stored_key: str) -> None:
    scenario_path = AGENT_FIXTURES / "success_writes_file.jsonl"
    info = runner(tmp_path, scenario_path).detect()
    assert info.usable and info.billing == "api" and info.auth_method == "api key from keychain"
    assert info.version == "0.2.176, PATH Claude Code 2.1.316"
    assert set(info.policy_parts) == {"planner", "implementer", "reviewer"}

    windows = runner(tmp_path, scenario_path, platform="win32").detect()
    assert not windows.policy_enforceable and "WSL2" in (windows.reason or "")
    assert not any(windows.policy_parts["implementer"].values())

    old = runner(tmp_path, scenario_path, "--version-string", "2.1.200").detect()
    assert old.reason == "Claude Code 2.1.200 is too old; SpoolHQ needs 2.1.259 or newer"

    missing = AgentSdkRunner(cli_cmd=[str(tmp_path / "no-such-claude")]).detect()
    assert (missing.installed, missing.version) == (False, "0.2.176")


def test_a_refused_role_never_starts(tmp_path: Path, policy: AgentPolicy, stored_key: str) -> None:
    sdk = runner(tmp_path, AGENT_FIXTURES / "success_writes_file.jsonl", platform="win32")
    with pytest.raises(BackendUnavailableError, match="WSL2"):
        run(sdk, policy)


def test_the_recorded_cli_stream_replays(
    tmp_path: Path, policy: AgentPolicy, stored_key: str
) -> None:
    """The stream real Claude Code 2.1.316 sent through this backend (a local stand-in
    API scripted the model's calls), replayed with the hook asked again."""
    recorded = AGENT_FIXTURES / "recorded" / "agent_sdk_run.jsonl"
    lines = recorded.read_text(encoding="utf-8").splitlines()
    worktree = json.dumps(str(policy.worktree))[1:-1]  # escaped: Windows backslashes
    path = tmp_path / "recorded.jsonl"
    path.write_text("\n".join(lines).replace("/work/wt", worktree) + "\n", encoding="utf-8")
    result, events, _ = run(runner(tmp_path, path), policy)
    assert result.outcome is Outcome.COMPLETED
    assert result.files_changed == ("hello.txt",)
    assert [event.tool for event in events if isinstance(event, PermissionDenied)] == [
        "Bash",
        "Bash",
        "Read",
    ]
    assert (policy.worktree / "hello.txt").read_text(encoding="utf-8") == "hello from spoolhq\n"
