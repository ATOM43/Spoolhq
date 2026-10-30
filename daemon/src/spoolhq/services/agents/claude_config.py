"""Claude Code's configuration for one run: the command line, the settings and the environment.

``build_argv`` and ``sandbox_settings`` turn an ``AgentPolicy`` into Claude Code's flags
and ``--settings`` object, ``child_env`` builds the allowlisted environment, and
``check_worktree`` refuses a worktree the sandbox could not protect. The scrub stubs
Claude Code leaves in its working folder are cleaned up here too. See ``docs/agents.md``.
"""

import dataclasses
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from spoolhq.core.agent_policy import allowed_env
from spoolhq.services.agents.claude_stream import CLAUDE_TOOLS, FILE_TOOLS, READ_ONLY_TOOLS
from spoolhq.services.agents.model import AgentPolicy, Billing, Budget, PolicyError

API_KEY_VAR = "ANTHROPIC_API_KEY"
AUTH_TOKEN_VAR = "ANTHROPIC_AUTH_TOKEN"  # noqa: S105 - a variable name
BASE_URL_VAR = "ANTHROPIC_BASE_URL"
ENV_SET = {
    # Claude Code removes its own credentials from the environment of the commands
    # the agent runs.
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",  # SCRUB_VAR
    "DISABLE_AUTOUPDATER": "1",
    # pnpm 10 would otherwise try to install from the network before each `pnpm run`;
    # the deps come from the gates' install.
    "npm_config_verify_deps_before_run": "false",
}
# With CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1, Claude Code 2.1.302 reports (and uses) the
# "default" mode instead of dontAsk. With --permission-prompts none, every call that
# would prompt there is denied, as in dontAsk; any other mode stops the run.
PERMISSION_MODES = frozenset({"dontAsk", "default"})
SCRUB_VAR = "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB"

# Empty files and folders Claude Code 2.1.302 creates in its working folder when
# CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1 is set (mount points that write-protect them in the
# sandbox), and leaves behind. Removed after a run if they are new and still empty.
SCRUB_STUBS = (
    ".env",
    ".env.development",
    ".env.development.local",
    ".env.local",
    ".env.production",
    ".env.production.local",
    ".env.test",
    ".env.test.local",
    ".gitmodules",
    ".npmrc",
    ".yarnrc",
    ".yarnrc.yml",
    "bunfig.toml",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    ".claude",
    "node_modules",
)


def child_env(
    parent: Mapping[str, str],
    *,
    billing: Billing,
    platform: str,
    base_url: str | None = None,
    endpoint_token: str | None = None,
) -> dict[str, str]:
    """The only environment the ``claude`` process gets: an allowlist, plus ENV_SET.

    ``ANTHROPIC_API_KEY`` is passed only for API billing; with it, Claude Code would
    bill the API instead of the subscription. ``base_url`` becomes ``ANTHROPIC_BASE_URL``
    (https://code.claude.com/docs/en/env-vars); the parent's own value never passes.
    With ``base_url``, ``endpoint_token`` becomes ``ANTHROPIC_AUTH_TOKEN``, which Claude
    Code sends instead of the saved subscription login, and no API key is passed
    (https://code.claude.com/docs/en/authentication#authentication-precedence).
    """
    api_key = billing == "api" and base_url is None
    env = allowed_env(parent, platform=platform, extra={API_KEY_VAR} if api_key else ())
    env.update(ENV_SET)
    if base_url is not None:
        env[BASE_URL_VAR] = base_url
        if endpoint_token is not None:
            env[AUTH_TOKEN_VAR] = endpoint_token
    return env


def with_config_dir(policy: AgentPolicy, env: Mapping[str, str]) -> AgentPolicy:
    """``policy`` that also denies ``CLAUDE_CONFIG_DIR`` when ``env`` moves Claude Code's
    config folder away from ``~/.claude``."""
    config_dir = next(
        (value for name, value in env.items() if name.upper() == "CLAUDE_CONFIG_DIR"), None
    )
    if not config_dir or config_dir in policy.denied_read_paths:
        return policy
    return dataclasses.replace(policy, denied_read_paths=(*policy.denied_read_paths, config_dir))


def requested_tools(policy: AgentPolicy) -> tuple[str, ...]:
    """``--tools`` for ``policy``; ``init`` must list exactly these for a read-only one."""
    return READ_ONLY_TOOLS if policy.read_only else CLAUDE_TOOLS


def sandbox_settings(policy: AgentPolicy) -> dict[str, Any]:
    """The ``--settings`` object: a required OS sandbox, no network, no hooks."""
    return {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            # The default (true) would approve every sandboxed command, allowlist or not.
            "autoAllowBashIfSandboxed": False,
            "network": {
                "allowedDomains": list(policy.network_domains),
                "strictAllowlist": True,
            },
            "credentials": {
                "files": [{"path": path, "mode": "deny"} for path in policy.denied_read_paths]
            },
        },
        "disableAllHooks": True,
    }


def build_argv(
    claude_cmd: Sequence[str],
    policy: AgentPolicy,
    budget: Budget,
    *,
    billing: Billing,
    model: str | None = None,
) -> list[str]:
    """The full ``claude`` command line. The prompt is never part of it."""
    argv = [
        *claude_cmd,
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
        ",".join(requested_tools(policy)),
        "--allowedTools",
        *(READ_ONLY_TOOLS if policy.read_only else FILE_TOOLS),
        *policy.bash_rules(),
        "--disallowedTools",
        "WebFetch",
        "WebSearch",
        "mcp__*",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--max-turns",
        str(budget.max_turns),
    ]
    if billing == "api" and budget.max_usd is not None:
        argv += ["--max-budget-usd", str(budget.max_usd)]
    if model is not None:
        argv += ["--model", model]
    argv += ["--settings", json.dumps(sandbox_settings(policy), separators=(",", ":"))]
    return argv


def permission_modes(env: Mapping[str, str], argv: Sequence[str]) -> frozenset[str]:
    """The ``init`` permission modes a run accepts: ``dontAsk``, plus ``default`` only
    when the child environment really has ``CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1`` and
    the command line has ``--permission-prompts none``."""
    prompts_none = any(
        flag == "--permission-prompts" and value == "none"
        for flag, value in zip(argv, argv[1:], strict=False)
    )
    if env.get(SCRUB_VAR) == "1" and prompts_none:
        return PERMISSION_MODES
    return frozenset({"dontAsk"})


def existing_stubs(folder: Path) -> frozenset[str]:
    return frozenset(name for name in SCRUB_STUBS if os.path.lexists(folder / name))


def remove_new_stubs(folder: Path, existed: frozenset[str]) -> list[str]:
    """Remove the scrub stubs that weren't in ``folder`` before and are still empty.

    A stub with content, or a folder with any file in it, is the agent's work and kept.
    Returns the names removed.
    """
    removed: list[str] = []
    for name in SCRUB_STUBS:
        path = folder / name
        if name in existed or path.is_symlink():
            continue
        try:
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()
                removed.append(name)
            elif path.is_dir() and _remove_empty_tree(path):
                removed.append(name)
        except OSError:
            continue
    return removed


def _remove_empty_tree(path: Path) -> bool:
    """Remove ``path`` if it holds only (nested) empty folders; otherwise touch nothing."""
    walked = list(os.walk(path, topdown=False))
    for root, dirs, files in walked:
        if files or any(Path(root, name).is_symlink() for name in dirs):
            return False
    for root, _, _ in walked:
        os.rmdir(root)
    return True


def expand_home(path: str, home: Path) -> Path:
    return home / path[2:] if path.startswith("~/") else Path(path)


def check_worktree(policy: AgentPolicy, home: Path) -> None:
    """Refuse a worktree that would let the agent write the home folder or a denied path.

    Sandboxed commands may write anywhere in the worktree, so it must not be the home
    folder, contain it, or overlap a path whose reads are denied.
    """
    worktree = policy.worktree.resolve()
    home = home.resolve()
    if worktree == home or worktree in home.parents:
        raise PolicyError(f"worktree {worktree} must not contain the home folder {home}")
    for denied in policy.denied_read_paths:
        target = expand_home(denied, home).resolve()
        if target == worktree or worktree in target.parents or target in worktree.parents:
            raise PolicyError(f"worktree {worktree} overlaps {denied}, which agents may not read")
