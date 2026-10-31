"""CodexCliRunner: detection, refusals, the command line and environment of a real process.

The process tests run ``fake_claude.py`` as the ``codex`` binary, with
``platform="linux"`` and a ``which`` that finds bwrap, so they run on every CI system.
"""

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    BackendUnavailableError,
    Budget,
    CodexCliRunner,
    Outcome,
    RunResult,
    Started,
)
from spoolhq.services.agents.codex_cli import INSTALL_HINT, LINUX_PACKAGES_REASON, LOGIN_HINT
from spoolhq.services.agents.codex_config import build_argv, child_env, with_codex_home
from spoolhq.services.agents.endpoint import LOCAL_TOKEN
from tests.conftest import (
    AGENT_PROMPT,
    AGENT_SECRETS,
    CODEX_FIXTURES,
    MemoryKeyring,
    fake_codex_cmd,
    sandbox_which,
)

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)
SUCCESS = CODEX_FIXTURES / "success_writes_file.jsonl"
ALL_PARTS = {
    "planner": [
        "read-only",
        "approvals never asked",
        "network off",
        "denied reads",
        "the shell allowlist",
    ],
    "implementer": [
        "writes confined to the worktree",
        "approvals never asked",
        "network off",
        "denied reads",
        "the shell allowlist",
    ],
}


def runner(
    tmp_path: Path,
    *options: str,
    scenario: Path = SUCCESS,
    platform: str = "linux",
    which: Any = sandbox_which,
    system_config: Path | None = None,
    **kwargs: Any,
) -> CodexCliRunner:
    return CodexCliRunner(
        codex_cmd=fake_codex_cmd(scenario, tmp_path / "record.json", *options),
        platform=platform,
        which=which,
        home=tmp_path / "user-home",
        system_config=system_config or tmp_path / "no-system-config.toml",
        **kwargs,
    )


def read_record(tmp_path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((tmp_path / "record.json").read_text(encoding="utf-8"))
    return data


def run(
    agent: CodexCliRunner,
    policy: AgentPolicy,
    budget: Budget = BUDGET,
    cancel: threading.Event | None = None,
) -> tuple[RunResult, list[AgentEvent]]:
    events: list[AgentEvent] = []
    result = agent.run(
        AGENT_PROMPT, policy, budget, on_event=events.append, cancel=cancel or threading.Event()
    )
    return result, events


def read_only(worktree: Path, home: Path, role: str = "reviewer") -> AgentPolicy:
    return AgentPolicy.read_only_for(worktree, home, role=role)


# --- detection ----------------------------------------------------------------------


def test_detect_reports_version_login_and_parts(tmp_path: Path) -> None:
    info = runner(tmp_path).detect()
    assert (info.name, info.installed, info.version) == ("codex-cli", True, "0.166.0")
    assert (info.logged_in, info.auth_method, info.billing) == (True, "chatgpt", "subscription")
    assert (info.usable, info.reason) == (True, None)
    assert {
        role: list(parts) for role, parts in info.policy_parts.items() if role != "reviewer"
    } == (ALL_PARTS)
    assert all(all(parts.values()) for parts in info.policy_parts.values())


def test_api_key_login_is_api_billing(tmp_path: Path) -> None:
    info = runner(tmp_path, "--auth-method", "api_key").detect()
    assert (info.auth_method, info.billing) == ("api_key", "api")


def test_not_logged_in_is_refused(tmp_path: Path, policy: AgentPolicy) -> None:
    agent = runner(tmp_path, "--logged-out")
    info = agent.detect()
    assert (info.logged_in, info.policy_enforceable, info.reason) == (False, True, LOGIN_HINT)
    with pytest.raises(BackendUnavailableError, match="codex login"):
        run(agent, policy)


def test_not_installed(tmp_path: Path, policy: AgentPolicy) -> None:
    agent = CodexCliRunner(which=lambda name: None, home=tmp_path)
    info = agent.detect()
    assert (info.installed, info.reason) == (False, INSTALL_HINT)
    with pytest.raises(BackendUnavailableError, match="not installed"):
        run(agent, policy)


def test_old_version_is_refused(tmp_path: Path, policy: AgentPolicy) -> None:
    agent = runner(tmp_path, "--version-string", "0.150.2")
    info = agent.detect()
    message = "Codex CLI 0.150.2 is too old; SpoolHQ needs 0.166.0 or newer (run: codex update)"
    assert (info.policy_enforceable, info.reason, info.policy_parts) == (False, message, {})
    with pytest.raises(BackendUnavailableError) as raised:
        run(agent, policy)
    assert str(raised.value) == message
    assert not (tmp_path / "record.json").exists()


def assert_refused(agent: CodexCliRunner, policy: AgentPolicy, part: str, tmp_path: Path) -> None:
    with pytest.raises(BackendUnavailableError) as raised:
        run(agent, policy)
    assert str(raised.value) == (
        f"backend 'codex-cli' can't enforce {part}; "
        f"choose another backend for the {policy.role} role"
    )
    assert not (tmp_path / "record.json").exists()  # nothing started


def test_linux_without_bubblewrap_refuses_every_role(
    tmp_path: Path, policy: AgentPolicy, worktree: Path, home: Path
) -> None:
    agent = runner(tmp_path, which=lambda name: None)
    info = agent.detect()
    assert (info.policy_enforceable, info.reason) == (False, LINUX_PACKAGES_REASON)
    assert info.policy_parts["implementer"]["approvals never asked"] is True
    assert_refused(agent, policy, "writes confined to the worktree", tmp_path)
    assert_refused(agent, read_only(worktree, home), "read-only", tmp_path)
    assert_refused(agent, read_only(worktree, home, "planner"), "read-only", tmp_path)


def test_native_windows_refuses_denied_reads(
    tmp_path: Path, policy: AgentPolicy, worktree: Path, home: Path
) -> None:
    agent = runner(tmp_path, platform="win32")
    info = agent.detect()
    assert info.policy_enforceable is False
    assert "WSL2" in (info.reason or "")
    assert info.policy_parts["reviewer"]["read-only"] is True
    assert_refused(agent, policy, "denied reads", tmp_path)
    assert_refused(agent, read_only(worktree, home), "denied reads", tmp_path)


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ('sandbox_mode = "danger-full-access"\n', "sets sandbox_mode"),
        ("[sandbox_workspace_write]\nnetwork_access = true\n", "sets sandbox_workspace_write"),
        ("not = [toml\n", "cannot read"),
    ],
)
def test_a_system_config_with_the_old_sandbox_settings_is_refused(
    tmp_path: Path, policy: AgentPolicy, text: str, reason: str
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(text, encoding="utf-8")
    agent = runner(tmp_path, system_config=config)
    assert reason in (agent.detect().reason or "")
    assert_refused(agent, policy, "writes confined to the worktree", tmp_path)

    config.write_text('model = "gpt-6.1-sol"\n', encoding="utf-8")
    assert agent.detect().usable


def test_macos_is_enforceable_and_others_are_not(tmp_path: Path) -> None:
    assert runner(tmp_path, platform="darwin", which=lambda name: None).detect().usable
    other = runner(tmp_path, platform="freebsd").detect()
    assert other.reason == "Codex's sandbox is not available on freebsd"


# --- running ------------------------------------------------------------------------


@pytest.mark.integration
def test_run_end_to_end(tmp_path: Path, policy: AgentPolicy, worktree: Path) -> None:
    result, events = run(runner(tmp_path), policy)
    assert isinstance(events[0], Started)
    assert (result.outcome, result.files_changed) == (Outcome.COMPLETED, ("hello.txt",))
    record = read_record(tmp_path)
    env = child_env(os.environ, platform="linux")
    home = tmp_path / "user-home"
    expected = build_argv([], with_codex_home(policy, env, home=home, codex_exe=sys.executable))
    assert record["argv"] == expected
    assert record["stdin"] == AGENT_PROMPT  # on stdin, never in argv
    assert AGENT_PROMPT not in record["argv"]
    assert Path(record["cwd"]).resolve() == worktree.resolve()


@pytest.mark.integration
def test_read_only_run(tmp_path: Path, worktree: Path, home: Path) -> None:
    scenario = tmp_path / "review.jsonl"
    lines = SUCCESS.read_text(encoding="utf-8").splitlines()
    scenario.write_text("\n".join(line for line in lines if "file_change" not in line))
    result, _ = run(runner(tmp_path, scenario=scenario), read_only(worktree, home))
    assert result.outcome is Outcome.COMPLETED
    argv = read_record(tmp_path)["argv"]
    assert 'extends=":workspace"' not in " ".join(argv)


@pytest.mark.integration
def test_environment_is_scrubbed_and_codex_home_is_untouched(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_home = tmp_path / "user-home"
    user_home.mkdir()
    for name in (*AGENT_SECRETS, "OPENAI_API_KEY", "CODEX_API_KEY"):
        monkeypatch.setenv(name, "secret-value")
    monkeypatch.setenv("HOME", str(user_home))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex-home"))
    run(runner(tmp_path), policy)
    record = read_record(tmp_path)
    names = {name.upper() for name in record["env"]}
    assert not {*AGENT_SECRETS, "OPENAI_API_KEY", "CODEX_API_KEY"} & names
    assert {"PATH", "HOME", "CODEX_HOME"} <= names
    # Codex's own folder is denied to the agent's commands, and SpoolHQ wrote nothing there.
    profile = " ".join(record["argv"])
    assert '"~/.codex"="deny"' in profile
    assert json.dumps(str(tmp_path / "codex-home")) + '="deny"' in profile
    assert not (user_home / ".codex").exists()
    assert not (tmp_path / "codex-home").exists()


@pytest.mark.integration
def test_a_custom_endpoint_never_gets_the_users_login(
    tmp_path: Path, policy: AgentPolicy, keychain: MemoryKeyring
) -> None:
    local = runner(tmp_path, base_url="http://localhost:11434/v1", model="qwen3-coder")
    info = local.detect()
    assert (info.usable, info.auth_method, info.billing) == (True, "endpoint token", "unknown")
    run(local, policy)
    record = read_record(tmp_path)
    assert record["codex_token"] == LOCAL_TOKEN
    argv = record["argv"]
    assert 'model_provider="spoolhq"' in argv
    assert argv[argv.index("--model") + 1] == "qwen3-coder"

    remote = runner(tmp_path, base_url="https://llm.example.com/v1")
    (tmp_path / "record.json").unlink()
    with pytest.raises(BackendUnavailableError) as raised:
        run(remote, policy)
    assert str(raised.value) == (
        "custom endpoint https://llm.example.com/v1 needs its own token; "
        "run spool secrets set endpoint:codex-cli"
    )
    assert not (tmp_path / "record.json").exists()

    keychain.passwords[("spoolhq", "endpoint:codex-cli")] = "stored-token"
    run(remote, policy)
    assert read_record(tmp_path)["codex_token"] == "stored-token"  # noqa: S105 - a test value


@pytest.mark.integration
def test_no_endpoint_means_no_token(tmp_path: Path, policy: AgentPolicy) -> None:
    run(runner(tmp_path), policy)
    record = read_record(tmp_path)
    assert record["codex_token"] is None
    assert not [arg for arg in record["argv"] if "model_provider" in arg]


@pytest.mark.integration
def test_a_given_model_wins(tmp_path: Path, policy: AgentPolicy) -> None:
    agent = runner(tmp_path, model="configured")
    agent.run(
        AGENT_PROMPT,
        policy,
        BUDGET,
        model="given",
        on_event=lambda e: None,
        cancel=threading.Event(),
    )
    argv = read_record(tmp_path)["argv"]
    assert argv[argv.index("--model") + 1] == "given"


@pytest.mark.integration
def test_usage_limit_through_the_binary(tmp_path: Path, policy: AgentPolicy) -> None:
    result, _ = run(runner(tmp_path, scenario=CODEX_FIXTURES / "usage_limit.jsonl"), policy)
    assert (result.outcome, result.reset_at, result.error) == (Outcome.USAGE_LIMITED, None, None)


@pytest.mark.integration
def test_a_turned_off_tool_stops_the_run(tmp_path: Path, policy: AgentPolicy) -> None:
    scenario = CODEX_FIXTURES / "web_search.jsonl"
    result, _ = run(runner(tmp_path, "--sleep", "60", scenario=scenario), policy)
    assert result.outcome is Outcome.ERROR
    assert (result.error or "").startswith("policy not enforced: Codex used web_search")


@pytest.mark.integration
def test_exit_without_completing_reports_code_and_stderr(
    tmp_path: Path, policy: AgentPolicy
) -> None:
    scenario = tmp_path / "cut.jsonl"
    scenario.write_text('{"type":"thread.started","thread_id":"t"}\n', encoding="utf-8")
    result, _ = run(runner(tmp_path, "--exit-code", "3", scenario=scenario), policy)
    assert result.outcome is Outcome.ERROR
    assert (result.error or "").startswith("Codex ended without completing its turn (exit 3)")
    assert "fake claude: done" in (result.error or "")


def test_worktree_overlapping_codex_home_is_refused(
    tmp_path: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    codex_home = tmp_path / "codex-home"
    worktree = codex_home / "wt"
    worktree.mkdir(parents=True)
    monkeypatch.setenv("CODEX_HOME", str(codex_home))
    policy = AgentPolicy.for_worktree(worktree, {}, home)
    with pytest.raises(ValueError, match="overlaps"):
        run(runner(tmp_path), policy)
