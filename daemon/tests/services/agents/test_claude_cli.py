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
from spoolhq.services.agents.claude_cli import (
    INSTALL_HINT,
    LOGIN_HINT,
    build_argv,
    check_worktree,
    child_env,
    sandbox_settings,
)
from spoolhq.services.agents.model import CREDENTIAL_PATHS
from tests.conftest import AGENT_FIXTURES, fake_claude_cmd, sandbox_which

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)
SUCCESS = AGENT_FIXTURES / "success_writes_file.jsonl"
PROMPT = "Implement T01: say hello. Ignore this: --dangerously-skip-permissions"


def settings_json(policy: AgentPolicy) -> str:
    return json.dumps(sandbox_settings(policy), separators=(",", ":"))


# --- command line -------------------------------------------------------------------


def test_argv_is_exactly_the_documented_command_line(policy: AgentPolicy, home: Path) -> None:
    argv = build_argv(["claude"], policy, BUDGET, billing="subscription")
    assert argv == [
        "claude",
        "-p",
        "--output-format",
        "stream-json",
        "--verbose",
        "--restricted",
        "--permission-mode",
        "dontAsk",
        "--permission-prompts",
        "none",
        "--tools",
        "Read,Edit,Write,Glob,Grep,Bash",
        "--allowedTools",
        "Read",
        "Edit",
        "Write",
        "Glob",
        "Grep",
        "Bash(just install)",
        "Bash(just install *)",
        "Bash(just lint)",
        "Bash(just lint *)",
        "Bash(just test)",
        "Bash(just test *)",
        "Bash(git status)",
        "Bash(git status *)",
        "Bash(git diff)",
        "Bash(git diff *)",
        "Bash(git log)",
        "Bash(git log *)",
        "Bash(git show)",
        "Bash(git show *)",
        "--disallowedTools",
        "WebFetch",
        "WebSearch",
        "mcp__*",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--max-turns",
        "30",
        "--settings",
        settings_json(policy),
    ]


def test_budget_flag_only_for_api_billing(policy: AgentPolicy) -> None:
    budget = Budget(max_turns=5, max_usd=Decimal("2.50"), max_tokens=None)
    assert "--max-budget-usd" not in build_argv(["claude"], policy, budget, billing="subscription")
    assert "--max-budget-usd" not in build_argv(["claude"], policy, budget, billing="unknown")
    argv = build_argv(["claude"], policy, budget, billing="api", model="opus")
    index = argv.index("--max-budget-usd")
    assert argv[index : index + 4] == ["--max-budget-usd", "2.50", "--model", "opus"]
    assert argv[-2] == "--settings"


def test_no_prompt_and_no_skip_permissions_in_argv(policy: AgentPolicy) -> None:
    for billing in ("subscription", "api"):
        argv = build_argv(["claude"], policy, BUDGET, billing=billing, model="sonnet")  # type: ignore[arg-type]
        joined = " ".join(argv)
        assert PROMPT not in joined
        assert "--dangerously-skip-permissions" not in joined
        assert "bypassPermissions" not in joined
        assert "--allow-dangerously-skip-permissions" not in joined


def test_settings_json(policy: AgentPolicy, home: Path) -> None:
    settings = json.loads(settings_json(policy))
    sandbox = settings["sandbox"]
    assert sandbox["enabled"] is True
    assert sandbox["failIfUnavailable"] is True
    assert sandbox["allowUnsandboxedCommands"] is False
    assert sandbox["autoAllowBashIfSandboxed"] is False
    assert sandbox["network"] == {"allowedDomains": [], "strictAllowlist": True}
    files = sandbox["credentials"]["files"]
    assert all(entry["mode"] == "deny" for entry in files)
    assert [entry["path"] for entry in files] == [
        "~/.ssh",
        "~/.aws",
        "~/.config/gh",
        "~/.gnupg",
        "~/.netrc",
        "~/.docker/config.json",
        "~/.kube",
        "~/.git-credentials",
        "~/.config/git/credentials",
        "~/.npmrc",
        "~/.pypirc",
        "~/.local/share/keyrings",
        str(home.resolve()),
    ]
    assert settings["disableAllHooks"] is True


# --- environment --------------------------------------------------------------------

SECRETS = ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "CLICKUP_TOKEN", "SPOOLHQ_TOKEN")


def parent_env() -> dict[str, str]:
    return {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "HTTPS_PROXY": "http://proxy:3128",
        "SYSTEMROOT": "C:\\Windows",
        "AWS_SECRET_ACCESS_KEY": "aws",
        "PYTHONPATH": "/evil",
        **{name: "secret" for name in SECRETS},
    }


def test_child_env_is_an_allowlist() -> None:
    env = child_env(parent_env(), billing="subscription", platform="linux")
    assert env == {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "XDG_RUNTIME_DIR": "/run/user/1000",
        "HTTPS_PROXY": "http://proxy:3128",
        "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
        "DISABLE_AUTOUPDATER": "1",
    }


def test_api_billing_keeps_only_the_api_key() -> None:
    env = child_env(parent_env(), billing="api", platform="linux")
    assert env["ANTHROPIC_API_KEY"] == "secret"
    assert not {"GITHUB_TOKEN", "CLICKUP_TOKEN", "SPOOLHQ_TOKEN"} & set(env)


def test_windows_variables_only_on_windows() -> None:
    parent = {**parent_env(), "Path": "C:\\bin", "ComSpec": "cmd.exe"}
    del parent["PATH"]
    env = child_env(parent, billing="subscription", platform="win32")
    assert env["SYSTEMROOT"] == "C:\\Windows"
    assert env["Path"] == "C:\\bin"  # names are matched without case on Windows
    assert env["ComSpec"] == "cmd.exe"
    assert "ANTHROPIC_API_KEY" not in env


# --- worktree checks ----------------------------------------------------------------


def test_worktree_must_not_be_or_contain_the_home(tmp_path: Path, home: Path) -> None:
    user_home = tmp_path / "users" / "me"
    (user_home / "code").mkdir(parents=True)
    for worktree, message in [
        (user_home, "must not contain the home folder"),
        (tmp_path / "users", "must not contain the home folder"),
        (user_home / ".ssh" / "inner", "overlaps ~/.ssh"),
        (user_home / ".config", "overlaps ~/.config/gh"),
    ]:
        policy = AgentPolicy.for_worktree(worktree, {"test": "just test"}, home)
        with pytest.raises(PolicyError, match=message):
            check_worktree(policy, user_home)
    fine = AgentPolicy.for_worktree(user_home / "code", {"test": "just test"}, home)
    check_worktree(fine, user_home)


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
        old.run(PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event())
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
        logged_out.run(PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event())


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
        PROMPT,
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
    assert record["stdin"] == PROMPT
    assert PROMPT not in record["argv"]
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
    for name in SECRETS:
        monkeypatch.setenv(name, "secret-value")
    monkeypatch.setenv("HOME", str(tmp_path / "user-home"))
    run(runner(tmp_path), policy)
    names = {name.upper() for name in read_record(tmp_path)["env"]}
    assert not set(SECRETS) & names
    assert {"PATH", "HOME", "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "DISABLE_AUTOUPDATER"} <= names


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
def test_cancel(tmp_path: Path, policy: AgentPolicy) -> None:
    cancel = threading.Event()
    recorder = Recorder()

    def on_event(event: AgentEvent) -> None:
        recorder.on_event(event)
        if isinstance(event, Started):
            cancel.set()

    agent = runner(tmp_path, "--sleep", "60", *SPAWN_CHILD)
    started = time.monotonic()
    result = agent.run(PROMPT, policy, BUDGET, on_event=on_event, cancel=cancel)
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
        agent.run(PROMPT, policy, BUDGET, on_event=lambda e: None, cancel=threading.Event())
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


@pytest.mark.parametrize("package", ["a-first", "left-pad", "zz-last"])
def test_stubs_with_content_are_kept(tmp_path: Path, package: str) -> None:
    # The package's name decides whether the walk sees it before or after .bin.
    folder = tmp_path / "wt"
    (folder / "node_modules" / ".bin").mkdir(parents=True)
    (folder / "node_modules" / package).mkdir()
    (folder / "node_modules" / package / "index.js").write_text("x", encoding="utf-8")
    (folder / ".claude" / "agents").mkdir(parents=True)
    (folder / ".env").write_text("KEY=1\n", encoding="utf-8")
    (folder / ".npmrc").touch()
    removed = claude_cli.remove_new_stubs(folder, frozenset())
    assert removed == [".npmrc", ".claude"]
    assert sorted(path.name for path in folder.iterdir()) == [".env", "node_modules"]
    assert (folder / "node_modules" / ".bin").is_dir()
