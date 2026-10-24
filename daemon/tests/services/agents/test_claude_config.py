"""claude_config: the command line, the settings, the environment and the worktree check."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from spoolhq.services.agents import AgentPolicy, Budget, PolicyError, claude_config
from spoolhq.services.agents.claude_config import (
    build_argv,
    check_worktree,
    child_env,
    permission_modes,
    sandbox_settings,
)
from spoolhq.services.agents.claude_stream import ClaudeStreamParser, PolicyViolation
from tests.conftest import AGENT_PROMPT, AGENT_SECRETS

BUDGET = Budget(max_turns=30, max_usd=None, max_tokens=None)


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
        assert AGENT_PROMPT not in joined
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
        "~/.claude",
        "~/.claude.json",
        str(home.resolve()),
    ]
    assert settings["disableAllHooks"] is True


def test_claude_codes_own_files_are_denied(policy: AgentPolicy) -> None:
    files = [
        entry["path"]
        for entry in json.loads(settings_json(policy))["sandbox"]["credentials"]["files"]
    ]
    assert {"~/.claude", "~/.claude.json"} <= set(files)


def test_claude_config_dir_is_denied_when_set(policy: AgentPolicy) -> None:
    moved = claude_config.with_config_dir(
        policy, {"PATH": "/usr/bin", "CLAUDE_CONFIG_DIR": "/srv/cfg"}
    )
    files = [entry["path"] for entry in sandbox_settings(moved)["sandbox"]["credentials"]["files"]]
    assert {"~/.claude", "~/.claude.json", "/srv/cfg"} <= set(files)
    assert claude_config.with_config_dir(policy, {"PATH": "/usr/bin"}) == policy
    windows = claude_config.with_config_dir(policy, {"claude_config_dir": "C:\\cfg"})
    assert windows.denied_read_paths[-1] == "C:\\cfg"


def test_worktree_inside_the_claude_folder_is_refused(tmp_path: Path, home: Path) -> None:
    user_home = tmp_path / "user-home"
    worktree = user_home / ".claude" / "projects" / "x"
    policy = AgentPolicy.for_worktree(worktree, {"test": "just test"}, home)
    with pytest.raises(PolicyError, match="overlaps ~/.claude, which agents may not read"):
        check_worktree(policy, user_home)


# --- environment --------------------------------------------------------------------


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
        **{name: "secret" for name in AGENT_SECRETS},
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
        "npm_config_verify_deps_before_run": "false",
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


# --- scrub stubs ---------------------------------------------------------------------


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
    removed = claude_config.remove_new_stubs(folder, frozenset())
    assert removed == [".npmrc", ".claude"]
    assert sorted(path.name for path in folder.iterdir()) == [".env", "node_modules"]
    assert (folder / "node_modules" / ".bin").is_dir()


def test_read_only_argv_has_only_the_read_tools(worktree: Path, home: Path) -> None:
    policy = AgentPolicy.read_only_for(worktree, home)
    argv = build_argv(["claude"], policy, BUDGET, billing="subscription")

    assert argv[argv.index("--tools") + 1] == "Read,Glob,Grep"
    allowed = argv[argv.index("--allowedTools") + 1 : argv.index("--disallowedTools")]
    assert allowed == ["Read", "Glob", "Grep"]
    assert not any("Bash(" in arg or arg in ("Edit", "Write") for arg in argv)
    assert "Edit" not in argv[argv.index("--tools") + 1]
    # The other layers are unchanged.
    writing = build_argv(["claude"], AgentPolicy.for_worktree(worktree, {}, home), BUDGET,
                         billing="subscription")  # fmt: skip
    for flag in ("--restricted", "--strict-mcp-config", "--no-session-persistence"):
        assert flag in argv
    assert argv[argv.index("--permission-mode") + 1] == "dontAsk"
    assert argv[-1] == writing[-1]  # the same sandbox settings


def test_read_only_policy_has_no_commands(worktree: Path, home: Path) -> None:
    policy = AgentPolicy.read_only_for(worktree, home)
    assert policy.read_only
    assert policy.commands == ()
    assert policy.bash_rules() == ()
    writing = AgentPolicy.for_worktree(worktree, {}, home)
    assert policy.denied_read_paths == writing.denied_read_paths


# --- init permission mode -------------------------------------------------------------

INIT = {
    "type": "system",
    "subtype": "init",
    "tools": ["Bash", "Edit", "Glob", "Grep", "Read", "Write"],
    "model": "m",
    "permissionMode": "default",
}


def test_default_mode_needs_the_scrub_variable_and_no_prompts(
    policy: AgentPolicy, worktree: Path
) -> None:
    argv = build_argv(["claude"], policy, BUDGET, billing="subscription")
    env = child_env({"PATH": "/usr/bin"}, billing="subscription", platform="linux")
    no_prompts_flag = [arg for arg in argv if arg not in ("--permission-prompts", "none")]

    assert permission_modes(env, argv) == {"dontAsk", "default"}
    assert permission_modes({**env, "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "0"}, argv) == {"dontAsk"}
    assert permission_modes({"PATH": "/usr/bin"}, argv) == {"dontAsk"}
    assert permission_modes(env, no_prompts_flag) == {"dontAsk"}

    accepting = ClaudeStreamParser(
        worktree, billing="subscription", permission_modes=permission_modes(env, argv)
    )
    assert accepting.feed(INIT)[0].kind == "started"
    refusing = ClaudeStreamParser(
        worktree, billing="subscription", permission_modes=permission_modes({}, argv)
    )
    with pytest.raises(PolicyViolation, match="permission mode 'default', expected dontAsk"):
        refusing.feed(INIT)
