"""Codex CLI's command line, permission profile, environment and policy parts."""

import tomllib
from pathlib import Path
from typing import Any

import pytest

from spoolhq.services.agents import AgentPolicy
from spoolhq.services.agents.codex_config import (
    ALLOWLIST,
    APPROVALS,
    DENIED_READS,
    NETWORK,
    READ_ONLY,
    WRITES,
    build_argv,
    child_env,
    permission_profile,
    policy_parts,
    refusal,
    with_codex_home,
)
from spoolhq.services.agents.model import CREDENTIAL_PATHS
from tests.conftest import AGENT_PROMPT, AGENT_SECRETS

# Flags and modes that would weaken or skip Codex's sandbox or approvals.
FORBIDDEN = (
    "dangerously",
    "yolo",
    "danger-full-access",
    "full-auto",
    "approve-for-me",
    "skip-git-repo-check",
    "--sandbox",
    "--add-dir",
    "on-request",
    "auto_review",
)
OVERRIDES = [
    'approval_policy="never"',
    'default_permissions="spoolhq"',
    "<profile>",
    'web_search="disabled"',
    "features.apps=false",
    "features.plugins=false",
    "features.hooks=false",
    "features.multi_agent=false",
    "features.memories=false",
    "tools.view_image=false",
    "allow_login_shell=false",
    "shell_environment_policy.ignore_default_excludes=false",
    'history.persistence="none"',
    "check_for_update_on_startup=false",
]


def profile_of(argv: list[str]) -> dict[str, Any]:
    """The ``permissions.spoolhq`` table from ``argv``, parsed as TOML."""
    [override] = [arg for arg in argv if arg.startswith("permissions.spoolhq=")]
    table: dict[str, Any] = tomllib.loads(override)["permissions"]["spoolhq"]
    return table


def expected(policy: AgentPolicy, *extra: str) -> list[str]:
    head = ["codex", "exec", "--json", "--ephemeral", "--ignore-user-config", "--ignore-rules"]
    argv = [*head, "--cd", str(policy.worktree), *extra]
    for override in OVERRIDES:
        if override == "<profile>":
            override = f"permissions.spoolhq={permission_profile(policy)}"
        argv += ["-c", override]
    return [*argv, "-"]


def test_argv_for_the_implementer(policy: AgentPolicy) -> None:
    argv = build_argv(["codex"], policy)
    assert argv == expected(policy)
    profile = profile_of(argv)
    assert profile["extends"] == ":workspace"
    assert profile["network"] == {"enabled": False}
    assert profile["filesystem"] == {path: "deny" for path in policy.denied_read_paths}
    assert set(CREDENTIAL_PATHS) <= set(profile["filesystem"])


def test_argv_for_a_read_only_role(worktree: Path, home: Path) -> None:
    for role in ("reviewer", "planner"):
        policy = AgentPolicy.read_only_for(worktree, home, role=role)
        argv = build_argv(["codex"], policy)
        assert argv == expected(policy)
        profile = profile_of(argv)
        assert "extends" not in profile  # no writes anywhere
        filesystem = profile["filesystem"]
        assert (filesystem[":root"], filesystem[":minimal"]) == ("deny", "read")
        assert filesystem[":workspace_roots"] == {".": "read"}
        assert "write" not in str(profile)
        assert all(filesystem[path] == "deny" for path in policy.denied_read_paths)
        assert profile["network"] == {"enabled": False}


def test_model_and_custom_endpoint(policy: AgentPolicy) -> None:
    argv = build_argv(
        ["codex"], policy, model="qwen3-coder", base_url='http://localhost:11434/v1?q="x"'
    )
    assert argv[argv.index("--model") + 1] == "qwen3-coder"
    flags = argv[argv.index("-c") : -1 : 2]
    assert 'model_provider="spoolhq"' in argv
    [provider] = [arg for arg in argv if arg.startswith("model_providers.spoolhq=")]
    assert tomllib.loads(provider)["model_providers"]["spoolhq"] == {
        "name": "SpoolHQ endpoint",
        "base_url": 'http://localhost:11434/v1?q="x"',
        "env_key": "SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI",
    }
    assert "requires_openai_auth" not in provider  # so no ChatGPT login is sent there
    assert set(flags) == {"-c"}
    assert "model_provider" not in " ".join(build_argv(["codex"], policy))


def test_no_bypass_flag_and_no_prompt(policy: AgentPolicy, worktree: Path, home: Path) -> None:
    for each in (policy, AgentPolicy.read_only_for(worktree, home)):
        argv = build_argv(["codex"], each, model="m", base_url="https://llm.example.com")
        assert argv[-1] == "-"  # the prompt comes from stdin
        assert AGENT_PROMPT not in argv
        assert not [arg for arg in argv for word in FORBIDDEN if word in arg]


def test_paths_are_quoted_for_toml(tmp_path: Path) -> None:
    worktree = tmp_path / 'a "quoted" \\ tree'
    worktree.mkdir()
    policy = AgentPolicy.for_worktree(worktree, {}, tmp_path / "spool-home")
    odd = with_codex_home(policy, {"CODEX_HOME": 'C:\\Users\\me\\"codex"'})
    profile = profile_of(build_argv(["codex"], odd))
    assert profile["filesystem"]['C:\\Users\\me\\"codex"'] == "deny"


def test_codex_home_is_denied(policy: AgentPolicy) -> None:
    assert with_codex_home(policy, {}).denied_read_paths == (*policy.denied_read_paths, "~/.codex")
    custom = with_codex_home(policy, {"CODEX_HOME": "/srv/codex"})
    assert custom.denied_read_paths[-2:] == ("~/.codex", "/srv/codex")
    assert with_codex_home(custom, {"CODEX_HOME": "/srv/codex"}) == custom


def test_child_env_is_an_allowlist() -> None:
    parent = {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "CODEX_HOME": "/home/me/.codex-alt",
        "CODEX_CA_CERTIFICATE": "/etc/ssl/corp.pem",
        "OPENAI_API_KEY": "sk-secret",
        "CODEX_API_KEY": "sk-secret",
        "SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI": "parent-token",
        **{name: "secret" for name in AGENT_SECRETS},
    }
    env = child_env(parent, platform="linux")
    assert env == {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "CODEX_HOME": "/home/me/.codex-alt",
        "CODEX_CA_CERTIFICATE": "/etc/ssl/corp.pem",
        "npm_config_verify_deps_before_run": "false",
    }
    with_token = child_env(parent, platform="linux", endpoint_token="spool-token")  # noqa: S106
    assert set(with_token) - set(env) == {"SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI"}
    assert with_token["SPOOLHQ_ENDPOINT_TOKEN_CODEX_CLI"] == "spool-token"  # noqa: S105


def test_every_part_is_enforced_with_the_sandbox() -> None:
    parts = policy_parts(sandbox=True, denied_reads=True)
    assert parts == {
        "planner": dict.fromkeys((READ_ONLY, APPROVALS, NETWORK, DENIED_READS, ALLOWLIST), True),
        "implementer": dict.fromkeys((WRITES, APPROVALS, NETWORK, DENIED_READS, ALLOWLIST), True),
        "reviewer": dict.fromkeys((READ_ONLY, APPROVALS, NETWORK, DENIED_READS, ALLOWLIST), True),
    }


@pytest.mark.parametrize(
    ("sandbox", "denied_reads", "role", "part"),
    [
        (False, True, "implementer", WRITES),
        (False, True, "reviewer", READ_ONLY),
        (False, True, "planner", READ_ONLY),
        (True, False, "implementer", DENIED_READS),
        (True, False, "reviewer", DENIED_READS),
    ],
)
def test_a_missing_part_is_refused_by_name(
    sandbox: bool, denied_reads: bool, role: str, part: str, worktree: Path, home: Path
) -> None:
    if role == "implementer":
        policy = AgentPolicy.for_worktree(worktree, {}, home)
    else:
        policy = AgentPolicy.read_only_for(worktree, home, role=role)
    parts = policy_parts(sandbox=sandbox, denied_reads=denied_reads)
    assert refusal(policy, parts) == (
        f"backend 'codex-cli' can't enforce {part}; choose another backend for the {role} role"
    )
    assert refusal(policy, policy_parts(sandbox=True, denied_reads=True)) is None


def test_each_part_is_checked(policy: AgentPolicy) -> None:
    for part in (WRITES, APPROVALS, NETWORK, DENIED_READS, ALLOWLIST):
        parts = policy_parts(sandbox=True, denied_reads=True)
        parts["implementer"][part] = False
        message = refusal(policy, parts)
        assert message is not None
        assert f"can't enforce {part};" in message
    assert refusal(policy, {}) is not None  # no parts known: nothing is assumed
