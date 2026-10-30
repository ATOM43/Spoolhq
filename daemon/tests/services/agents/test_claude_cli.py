"""ClaudeCliRunner: command line, settings, environment, detection and real processes.

The process tests run ``fake_claude.py`` as the ``claude`` binary, with
``platform="linux"`` and a ``which`` that finds bwrap and socat, so they run on every
CI operating system.
"""

import json
import os
import sys
import threading
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import (
    AgentEvent,
    AgentPolicy,
    BackendUnavailableError,
    Budget,
    ClaudeCliRunner,
    Outcome,
    PermissionDenied,
    PolicyError,
    Started,
    claude_cli,
)
from spoolhq.services.agents.claude_cli import INSTALL_HINT, LOGIN_HINT
from spoolhq.services.agents.claude_config import build_argv
from spoolhq.services.agents.model import CREDENTIAL_PATHS
from tests.conftest import (
    AGENT_FIXTURES,
    AGENT_PROMPT,
    AGENT_SECRETS,
    fake_claude_cmd,
    sandbox_which,
)

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)
SUCCESS = AGENT_FIXTURES / "success_writes_file.jsonl"


# --- detection ----------------------------------------------------------------------


def runner(
    tmp_path: Path,
    *options: str,
    scenario: Path = SUCCESS,
    platform: str = "linux",
    which: Any = sandbox_which,
    user_home: Path | None = None,
) -> ClaudeCliRunner:
    record = tmp_path / "record.json"
    return ClaudeCliRunner(
        claude_cmd=fake_claude_cmd(scenario, record, *options),
        platform=platform,
        which=which,
        home=user_home or tmp_path / "user-home",
    )


def read_record(tmp_path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((tmp_path / "record.json").read_text(encoding="utf-8"))
    return data


@pytest.mark.integration
def test_detect_reports_version_login_and_billing(tmp_path: Path) -> None:
    info = runner(tmp_path).detect()
    assert info.name == "claude-code-cli"
    assert (info.installed, info.version) == (True, "2.1.302")
    assert (info.logged_in, info.auth_method, info.billing) == (True, "claude.ai", "subscription")
    assert (info.policy_enforceable, info.reason) == (True, None)
    assert info.usable


@pytest.mark.integration
@pytest.mark.parametrize(
    ("method", "billing"),
    [("oauth_token", "subscription"), ("api_key_helper", "api"), ("third_party", "unknown")],
)
def test_billing_follows_the_auth_method(tmp_path: Path, method: str, billing: str) -> None:
    assert runner(tmp_path, "--auth-method", method).detect().billing == billing


@pytest.mark.integration
def test_old_version_is_refused(tmp_path: Path, policy: AgentPolicy) -> None:
    old = runner(tmp_path, "--version-string", "2.1.200")
    info = old.detect()
    message = "Claude Code 2.1.200 is too old; SpoolHQ needs 2.1.259 or newer (run: claude update)"
    assert (info.version, info.policy_enforceable, info.reason) == ("2.1.200", False, message)
    with pytest.raises(BackendUnavailableError) as exc:
        old.run(AGENT_PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event())
    assert str(exc.value) == message
    assert not (tmp_path / "record.json").exists()


@pytest.mark.integration
def test_unreadable_version_is_refused(tmp_path: Path) -> None:
    info = runner(tmp_path, "--version-string", "unknown").detect()
    assert info.installed
    assert info.version == "unknown (Claude Code)"
    assert info.reason == (
        "cannot read Claude Code's version from 'unknown (Claude Code)'; "
        "SpoolHQ needs 2.1.259 or newer (run: claude update)"
    )


@pytest.mark.integration
def test_not_logged_in_raises(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    logged_out = runner(tmp_path, "--logged-out")
    info = logged_out.detect()
    assert (info.logged_in, info.auth_method, info.billing) == (False, "none", "unknown")
    assert info.policy_enforceable
    assert info.reason == LOGIN_HINT
    with pytest.raises(BackendUnavailableError, match="claude auth login"):
        logged_out.run(
            AGENT_PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event()
        )


def test_not_installed(tmp_path: Path) -> None:
    info = ClaudeCliRunner(which=lambda name: None).detect()
    assert (info.installed, info.logged_in, info.policy_enforceable) == (False, False, False)
    assert info.reason == INSTALL_HINT
    missing = ClaudeCliRunner(claude_cmd=[str(tmp_path / "no-such-claude")]).detect()
    assert not missing.installed


@pytest.mark.integration
def test_failing_version_command_means_not_installed(tmp_path: Path) -> None:
    broken = ClaudeCliRunner(claude_cmd=[sys.executable, "-c", "raise SystemExit(2)"])
    assert not broken.detect().installed


def test_native_windows_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claude_cli.ClaudeCliRunner, "_probe", fake_probe)
    info = ClaudeCliRunner(claude_cmd=["claude"], platform="win32").detect()
    assert info.installed and info.logged_in
    assert not info.policy_enforceable
    assert info.reason is not None and "WSL2" in info.reason


def test_linux_needs_bubblewrap_and_socat(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claude_cli.ClaudeCliRunner, "_probe", fake_probe)
    for missing in ("bwrap", "socat"):

        def which(name: str, missing: str = missing) -> str | None:
            return None if name == missing else f"/usr/bin/{name}"

        info = ClaudeCliRunner(claude_cmd=["claude"], platform="linux", which=which).detect()
        assert not info.policy_enforceable
        assert info.reason is not None
        assert "bubblewrap and socat" in info.reason
        assert "sudo dnf install bubblewrap socat" in info.reason


def test_macos_is_enforceable_and_others_are_not(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(claude_cli.ClaudeCliRunner, "_probe", fake_probe)
    assert ClaudeCliRunner(claude_cmd=["claude"], platform="darwin").detect().policy_enforceable
    other = ClaudeCliRunner(claude_cmd=["claude"], platform="freebsd14").detect()
    assert other.reason == "Claude Code's Bash sandbox is not available on freebsd14"


def test_auth_status_that_is_not_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def probe(self: ClaudeCliRunner, argv: list[str], env: dict[str, str]) -> tuple[int, str]:
        return (0, "2.1.302 (Claude Code)") if argv[-1] == "--version" else (0, "[1]")

    monkeypatch.setattr(claude_cli.ClaudeCliRunner, "_probe", probe)
    info = ClaudeCliRunner(claude_cmd=["claude"], platform="darwin").detect()
    assert (info.logged_in, info.auth_method) == (True, None)
    assert info.billing == "unknown"


def fake_probe(self: ClaudeCliRunner, argv: list[str], env: dict[str, str]) -> tuple[int, str]:
    if argv[-1] == "--version":
        return 0, "2.1.302 (Claude Code)\n"
    return 0, json.dumps({"loggedIn": True, "authMethod": "claude.ai"})


# --- running ------------------------------------------------------------------------


class Recorder:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []
        self.raw: list[dict[str, Any]] = []
        self.threads: set[int] = set()

    def on_event(self, event: AgentEvent) -> None:
        self.threads.add(threading.get_ident())
        self.events.append(event)

    def on_raw(self, message: dict[str, Any]) -> None:
        self.threads.add(threading.get_ident())
        self.raw.append(message)


def run(
    agent: ClaudeCliRunner,
    policy: AgentPolicy,
    budget: Budget = BUDGET,
    recorder: Recorder | None = None,
    cancel: threading.Event | None = None,
) -> Any:
    recorder = recorder or Recorder()
    return agent.run(
        AGENT_PROMPT,
        policy,
        budget,
        on_event=recorder.on_event,
        on_raw=recorder.on_raw,
        cancel=cancel or threading.Event(),
    )


@pytest.mark.integration
def test_run_end_to_end(tmp_path: Path, policy: AgentPolicy) -> None:
    recorder = Recorder()
    result = run(runner(tmp_path), policy, recorder=recorder)
    assert result.outcome is Outcome.COMPLETED
    assert result.files_changed == ("hello.txt",)
    assert (result.input_tokens, result.output_tokens, result.cost_micro_usd) == (1200, 300, None)
    assert (result.backend, result.backend_version) == ("claude-code-cli", "2.1.302")

    record = read_record(tmp_path)
    assert record["stdin"] == AGENT_PROMPT
    assert AGENT_PROMPT not in record["argv"]
    assert record["argv"] == build_argv([], policy, BUDGET, billing="subscription")

    # Callbacks: every raw line in order, events in stream order, on one thread.
    lines = SUCCESS.read_text(encoding="utf-8").splitlines()
    assert recorder.raw == [json.loads(line) for line in lines]
    assert [event.kind for event in recorder.events] == [
        "started",
        "usage",
        "message",
        "tool_call",
        "file_edit",
        "usage",
        "message",
        "rate_limit",
    ]
    assert recorder.threads == {threading.get_ident()}


@pytest.mark.integration
def test_environment_is_scrubbed(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in AGENT_SECRETS:
        monkeypatch.setenv(name, "secret-value")
    monkeypatch.setenv("HOME", str(tmp_path / "user-home"))
    run(runner(tmp_path), policy)
    names = {name.upper() for name in read_record(tmp_path)["env"]}
    assert not set(AGENT_SECRETS) & names
    assert {"PATH", "HOME", "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "DISABLE_AUTOUPDATER"} <= names


@pytest.mark.integration
def test_pnpm_skips_its_dependency_check_in_the_child(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("npm_config_verify_deps_before_run", raising=False)
    run(runner(tmp_path), policy)
    # The record has names only; test_child_env_is_an_allowlist checks the value.
    names = {name.lower() for name in read_record(tmp_path)["env"]}
    assert "npm_config_verify_deps_before_run" in names


PROXY_AND_CA = {
    "https_proxy": "http://proxy:3128",
    "http_proxy": "http://proxy:3128",
    "no_proxy": "localhost,127.0.0.1",
    "NODE_EXTRA_CA_CERTS": "/etc/ssl/corp.pem",
    "SSL_CERT_FILE": "/etc/ssl/certs.pem",
}


@pytest.mark.integration
def test_proxy_and_ca_variables_reach_claude(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name, value in PROXY_AND_CA.items():
        monkeypatch.setenv(name, value)
    run(runner(tmp_path), policy)
    names = set(read_record(tmp_path)["env"])
    if sys.platform == "win32":  # names ignore case there
        assert {name.upper() for name in PROXY_AND_CA} <= {name.upper() for name in names}
    else:
        assert set(PROXY_AND_CA) <= names


@pytest.mark.integration
def test_claude_config_dir_reaches_the_settings(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    config_dir = str(tmp_path / "cfg")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", config_dir)
    run(runner(tmp_path), policy)
    argv = read_record(tmp_path)["argv"]
    settings = json.loads(argv[argv.index("--settings") + 1])
    assert config_dir in [entry["path"] for entry in settings["sandbox"]["credentials"]["files"]]


@pytest.mark.integration
def test_custom_endpoint_and_model_reach_the_child_only(
    tmp_path: Path, policy: AgentPolicy, user_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(user_home))
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://parent.example.com")  # never passed on
    run(runner(tmp_path, user_home=user_home), policy)
    plain = read_record(tmp_path)
    assert plain["argv"] == build_argv([], policy, BUDGET, billing="subscription")
    assert plain["base_url"] is None

    custom = ClaudeCliRunner(
        claude_cmd=fake_claude_cmd(SUCCESS, tmp_path / "record.json"),
        platform="linux",
        which=sandbox_which,
        home=user_home,
        base_url="http://localhost:11434",
        model="qwen3-coder",
    )
    run(custom, policy)
    record = read_record(tmp_path)
    expected = build_argv([], policy, BUDGET, billing="subscription", model="qwen3-coder")
    assert record["argv"] == expected
    assert record["base_url"] == "http://localhost:11434"
    assert set(record["env"]) - set(plain["env"]) == {"ANTHROPIC_BASE_URL"}
    # Passed per child; Claude Code's own config is never written.
    assert not (user_home / ".claude").exists()
    assert not (user_home / ".claude.json").exists()

    # A model given to run() wins over the configured one.
    cancel = threading.Event()
    custom.run(AGENT_PROMPT, policy, BUDGET, model="given", on_event=lambda e: None, cancel=cancel)
    argv = read_record(tmp_path)["argv"]
    assert argv[argv.index("--model") + 1] == "given"


@pytest.mark.integration
def test_api_key_billing_passes_the_key_and_the_budget(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    agent = runner(tmp_path, "--logged-out")
    assert (agent.detect().billing, agent.detect().auth_method) == ("api", "api_key")
    budget = Budget(max_turns=3, max_usd=Decimal("1.25"), max_tokens=None)
    result = run(agent, policy, budget)
    assert result.cost_micro_usd == 12300
    record = read_record(tmp_path)
    assert "ANTHROPIC_API_KEY" in {name.upper() for name in record["env"]}
    assert record["argv"][record["argv"].index("--max-budget-usd") + 1] == "1.25"


@pytest.mark.integration
def test_permission_denied_through_the_binary(
    tmp_path: Path, policy: AgentPolicy, caplog: pytest.LogCaptureFixture
) -> None:
    recorder = Recorder()
    agent = runner(tmp_path, scenario=AGENT_FIXTURES / "permission_denied.jsonl")
    result = run(agent, policy, recorder=recorder)
    denied = [event for event in recorder.events if isinstance(event, PermissionDenied)]
    assert [event.tool for event in denied] == ["Bash"]
    assert result.denials == tuple(denied)
    assert any("python3" in record.getMessage() for record in caplog.records)


@pytest.mark.integration
def test_usage_limit_through_the_binary(tmp_path: Path, policy: AgentPolicy) -> None:
    from tests.services.agents.test_claude_stream import RESET

    agent = runner(tmp_path, scenario=AGENT_FIXTURES / "usage_limit.jsonl")
    result = run(agent, policy)
    assert (result.outcome, result.reset_at, result.error) == (Outcome.USAGE_LIMITED, RESET, None)


@pytest.mark.integration
def test_unexpected_tool_in_init_stops_the_run(tmp_path: Path, policy: AgentPolicy) -> None:
    agent = runner(tmp_path, "--sleep", "60", scenario=AGENT_FIXTURES / "extra_tool_in_init.jsonl")
    started = time.monotonic()
    recorder = Recorder()
    result = run(agent, policy, recorder=recorder)
    assert time.monotonic() - started < 30
    assert result.outcome is Outcome.ERROR
    assert result.error is not None
    assert result.error.startswith("policy not enforced: init lists tools that were not requested")
    assert recorder.events == []


@pytest.mark.integration
def test_default_permission_mode_from_env_scrub_is_accepted(
    tmp_path: Path, policy: AgentPolicy
) -> None:
    # Claude Code 2.1.302 reports "default" when CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1.
    scenario = tmp_path / "default-mode.jsonl"
    lines = SUCCESS.read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    scenario.write_text(
        "\n".join([json.dumps({**first, "permissionMode": "default"}), *lines[1:]]),
        encoding="utf-8",
    )
    assert run(runner(tmp_path, scenario=scenario), policy).outcome is Outcome.COMPLETED
    first["permissionMode"] = "acceptEdits"
    scenario.write_text("\n".join([json.dumps(first), *lines[1:]]), encoding="utf-8")
    result = run(runner(tmp_path, scenario=scenario), policy)
    assert result.outcome is Outcome.ERROR
    assert "permission mode 'acceptEdits'" in (result.error or "")


@pytest.mark.integration
def test_token_budget_stops_the_run(tmp_path: Path, policy: AgentPolicy) -> None:
    budget = Budget(max_turns=30, max_usd=None, max_tokens=500)
    result = run(runner(tmp_path, "--sleep", "60"), policy, budget)
    assert result.outcome is Outcome.BUDGET_EXHAUSTED
    assert result.error is None


# A grandchild process, to check the whole process group is stopped (POSIX only:
# on Windows, terminate() stops only claude itself).
SPAWN_CHILD = ("--spawn-child",) if sys.platform != "win32" else ()


def assert_gone(pid: int) -> None:
    """Fail unless ``pid`` exits within 10 s (POSIX only)."""
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return
        time.sleep(0.05)
    pytest.fail(f"process {pid} is still running")


@pytest.mark.integration
def test_timeout(tmp_path: Path, policy: AgentPolicy) -> None:
    budget = Budget(max_turns=30, max_usd=None, max_tokens=None, timeout_s=1)
    started = time.monotonic()
    result = run(runner(tmp_path, "--sleep", "60", *SPAWN_CHILD), policy, budget)
    assert result.outcome is Outcome.TIMED_OUT
    assert result.files_changed == ("hello.txt",)
    assert time.monotonic() - started < 30
    if sys.platform != "win32":
        record = read_record(tmp_path)
        assert_gone(record["pid"])
        assert_gone(record["child_pid"])


@pytest.mark.integration
@pytest.mark.skipif(sys.platform == "win32", reason="Windows stops with terminate() then kill()")
@pytest.mark.parametrize("ignored", [("--ignore-sigint",), ("--ignore-sigint", "--ignore-sigterm")])
def test_stop_escalates_to_sigterm_and_sigkill(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch, ignored: tuple[str, ...]
) -> None:
    monkeypatch.setattr(claude_cli, "INTERRUPT_WAIT_S", 0.5)
    monkeypatch.setattr(claude_cli, "TERMINATE_WAIT_S", 0.5)
    budget = Budget(max_turns=30, max_usd=None, max_tokens=None, timeout_s=1)
    started = time.monotonic()
    result = run(runner(tmp_path, "--sleep", "60", *ignored), policy, budget)
    assert result.outcome is Outcome.TIMED_OUT
    assert time.monotonic() - started < 15
    pid = read_record(tmp_path)["pid"]
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_cancel(tmp_path: Path, policy: AgentPolicy) -> None:
    cancel = threading.Event()
    recorder = Recorder()

    def on_event(event: AgentEvent) -> None:
        recorder.on_event(event)
        if isinstance(event, Started):
            cancel.set()

    agent = runner(tmp_path, "--sleep", "60", *SPAWN_CHILD)
    started = time.monotonic()
    result = agent.run(AGENT_PROMPT, policy, BUDGET, on_event=on_event, cancel=cancel)
    assert result.outcome is Outcome.CANCELLED
    assert result.error is None
    assert time.monotonic() - started < 30
    if sys.platform != "win32":
        record = read_record(tmp_path)
        assert_gone(record["pid"])
        assert_gone(record["child_pid"])


@pytest.mark.integration
def test_exit_without_result_reports_code_and_stderr(tmp_path: Path, policy: AgentPolicy) -> None:
    scenario = tmp_path / "init-only.jsonl"
    lines = SUCCESS.read_text(encoding="utf-8").splitlines()
    scenario.write_text(f"{lines[0]}\nnot json\n[1]\n\n", encoding="utf-8")
    result = run(runner(tmp_path, "--exit-code", "3", scenario=scenario), policy)
    assert result.outcome is Outcome.ERROR
    assert result.error == "Claude Code ended without a result (exit 3)\nfake claude: done"
    assert result.debug == {"unknown_events": 0, "invalid_lines": 2}


@pytest.mark.integration
def test_worktree_overlapping_the_home_is_refused(tmp_path: Path, home: Path) -> None:
    user_home = tmp_path / "user-home"
    policy = AgentPolicy.for_worktree(user_home, {"test": "just test"}, home)
    with pytest.raises(PolicyError, match="must not contain the home folder"):
        run(runner(tmp_path, user_home=user_home), policy)
    assert not (tmp_path / "record.json").exists()


@pytest.mark.integration
def test_oversized_prompt_is_refused(
    tmp_path: Path, policy: AgentPolicy, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(claude_cli, "MAX_PROMPT_BYTES", 10)
    with pytest.raises(ValueError, match="10 MB"):
        run(runner(tmp_path), policy)


def test_unusable_backend_raises_before_starting(policy: AgentPolicy) -> None:
    agent = ClaudeCliRunner(which=lambda name: None)
    with pytest.raises(BackendUnavailableError) as exc:
        agent.run(AGENT_PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event())
    assert str(exc.value) == INSTALL_HINT


def test_policy_fields_are_untouched_by_credentials_list(policy: AgentPolicy) -> None:
    assert policy.denied_read_paths[: len(CREDENTIAL_PATHS)] == CREDENTIAL_PATHS


# --- scrub stubs ---------------------------------------------------------------------


@pytest.mark.integration
def test_detect_leaves_no_stubs_in_the_current_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    here = tmp_path / "here"
    here.mkdir()
    monkeypatch.chdir(here)
    assert runner(tmp_path, "--stubs").detect().usable
    assert list(here.iterdir()) == []


@pytest.mark.integration
def test_run_removes_new_empty_stubs_only(
    tmp_path: Path, worktree: Path, policy: AgentPolicy
) -> None:
    (worktree / "package.json").write_text('{"name": "app"}', encoding="utf-8")
    (worktree / ".env.local").write_text("", encoding="utf-8")  # empty, but was there
    result = run(runner(tmp_path, "--stubs"), policy)
    assert result.outcome is Outcome.COMPLETED
    assert sorted(path.name for path in worktree.iterdir()) == [".env.local", "package.json"]
    assert (worktree / "package.json").read_text(encoding="utf-8") == '{"name": "app"}'


@pytest.mark.integration
def test_read_only_run_through_the_binary(tmp_path: Path, worktree: Path, home: Path) -> None:
    from tests.conftest import REVIEW_FIXTURES

    policy = AgentPolicy.read_only_for(worktree, home)
    agent = runner(tmp_path, scenario=REVIEW_FIXTURES / "approve.jsonl")
    assert run(agent, policy).outcome is Outcome.COMPLETED
    argv = read_record(tmp_path)["argv"]
    assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"

    agent = runner(tmp_path, scenario=REVIEW_FIXTURES / "init_with_edit.jsonl")
    result = run(agent, policy)
    assert result.outcome is Outcome.ERROR
    assert result.error is not None
    assert result.error.startswith("policy not enforced: init lists tools that were not requested")
