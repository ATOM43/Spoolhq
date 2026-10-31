"""Codex CLI's configuration for one run: the command line, the permission profile, the
environment, and which policy parts Codex can enforce.

Everything goes through ``codex exec`` flags and ``-c key=value`` overrides; the user's
``~/.codex/config.toml`` is not loaded (``--ignore-user-config``) and nothing is written
to it. Checked against the Codex CLI 0.166.0 docs; see ``docs/agents.md`` and DECISIONS.
"""

import dataclasses
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from spoolhq.core.agent_policy import allowed_env
from spoolhq.services.agents.endpoint import token_var
from spoolhq.services.agents.model import AgentPolicy, denials_except

BACKEND_NAME = "codex-cli"
PROFILE = "spoolhq"
"""The permission profile SpoolHQ defines for each run (``-c permissions.spoolhq=…``)."""
PROVIDER = "spoolhq"
"""The model provider SpoolHQ defines for a custom endpoint."""
ENV_EXTRA = frozenset({"CODEX_HOME", "CODEX_CA_CERTIFICATE"})
"""Variables Codex documents that it reads, passed on when the daemon has them."""
ENV_SET = {
    # pnpm 10 would otherwise try to install from the network before each `pnpm run`;
    # the deps come from the gates' install.
    "npm_config_verify_deps_before_run": "false",
}
EXTRA_FEATURES_OFF = (
    "view_image",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "computer_use",
    "in_app_browser",
    "remote_plugin",
    "skill_mcp_dependency_install",
    "tool_suggest",
)
"""Features found on in real Codex 0.166.0 (``codex features list``) that the run must not use."""
CODEX_PATHS = ("~/.codex",)
"""Codex's own login and state: the agent's commands may not read them."""

# The policy parts, in the order a refusal names the first one missing.
WRITES = "writes confined to the worktree"
READ_ONLY = "read-only"
APPROVALS = "approvals never asked"
NETWORK = "network off"
DENIED_READS = "denied reads"
ALLOWLIST = "the shell allowlist"
ROLES = ("planner", "implementer", "reviewer")


def required_parts(read_only: bool) -> tuple[str, ...]:
    return (READ_ONLY if read_only else WRITES, APPROVALS, NETWORK, DENIED_READS, ALLOWLIST)


def policy_parts(*, sandbox: bool, denied_reads: bool) -> dict[str, dict[str, bool]]:
    """Role -> part -> whether Codex enforces it here.

    ``sandbox``: the OS sandbox runs Codex's permission profile (bubblewrap on Linux,
    Seatbelt on macOS). ``denied_reads``: its deny rules can be relied on here. Codex has
    no per-command allowlist; the OS sandbox with network off and denied reads stands in
    for it (DECISIONS), so the allowlist holds exactly when those do.
    """
    enforced = {
        WRITES: sandbox,
        READ_ONLY: sandbox,
        APPROVALS: True,  # approval_policy="never"
        NETWORK: sandbox,
        DENIED_READS: sandbox and denied_reads,
    }
    enforced[ALLOWLIST] = sandbox and denied_reads
    return {
        role: {part: enforced[part] for part in required_parts(role != "implementer")}
        for role in ROLES
    }


def refusal(
    policy: AgentPolicy, parts: Mapping[str, Mapping[str, bool]], backend: str = BACKEND_NAME
) -> str | None:
    """Why ``policy`` can't run on ``backend`` here, naming the first part it can't enforce."""
    enforced = parts.get(policy.role, {})
    for part in required_parts(policy.read_only):
        if not enforced.get(part, False):
            return (
                f"backend '{backend}' can't enforce {part}; "
                f"choose another backend for the {policy.role} role"
            )
    return None


SHARED_TEMP = ("/tmp", "/var/tmp")  # noqa: S108 - folders to refuse, never written to


def temp_folders(env: Mapping[str, str]) -> list[str]:
    """The shared temp folders Codex's ``:workspace`` profile lets the agent write in."""
    found = [*SHARED_TEMP, *filter(None, [env.get("TMPDIR")]), tempfile.gettempdir()]
    return list(dict.fromkeys(found))


def temp_worktree_refusal(worktree: Path, env: Mapping[str, str]) -> str | None:
    """Why Codex can't run in ``worktree`` (inside a shared temp folder), or None.

    Both sides are resolved, so a symlink into a temp folder (or macOS's ``/tmp`` →
    ``/private/tmp``) counts.
    """
    real = worktree.resolve()
    for folder in temp_folders(env):
        if real.is_relative_to(Path(folder).resolve()):
            return (
                f"backend '{BACKEND_NAME}' can't run in a worktree under {folder}: its sandbox "
                "can write anywhere there; set worktrees_dir outside temp folders"
            )
    return None


def install_dir(codex_exe: str) -> Path:
    """The folder Codex's binary ships in: the parent of its ``bin/`` (a standalone
    release, ``~/.codex/packages/standalone/releases/<version>``), else its own folder."""
    exe = Path(os.path.realpath(codex_exe))
    return exe.parent.parent if exe.parent.name == "bin" else exe.parent


def with_codex_home(
    policy: AgentPolicy, env: Mapping[str, str], *, home: Path, codex_exe: str
) -> AgentPolicy:
    """``policy`` that also denies Codex's own folder (``~/.codex`` and ``CODEX_HOME``).

    The standalone installer puts Codex itself under ``~/.codex/packages``, and Codex
    runs its own binary again inside the sandbox, so then everything in the folder is
    denied except the path down to the installed release (binaries only, no secrets).
    """
    install = install_dir(codex_exe)
    extra: list[str] = []
    for raw in [*CODEX_PATHS, *filter(None, [env.get("CODEX_HOME")])]:
        folder = (home / raw[2:] if raw.startswith("~/") else Path(raw)).resolve()
        inside = install.is_relative_to(folder) and install != folder
        extra += denials_except(folder, install) if inside else [raw]
    denied = [path for path in dict.fromkeys(extra) if path not in policy.denied_read_paths]
    return dataclasses.replace(policy, denied_read_paths=(*policy.denied_read_paths, *denied))


def _toml(value: str) -> str:
    # A JSON string is a valid TOML basic string.
    return json.dumps(value, ensure_ascii=False)


def permission_profile(policy: AgentPolicy, install: Path | None = None) -> str:
    """The profile as a TOML inline table, for ``-c permissions.spoolhq=…``.

    Writing: Codex's ``:workspace`` (writes to the workspace roots and temp folders, the
    worktree's ``.git`` read-only). Read-only: no writes, and reads only in the worktree
    and Codex's ``:minimal`` runtime paths. Both: every denied path ``deny`` (no reads,
    no writes) and no network for the agent's commands. ``install`` is Codex's own
    folder, readable in a read-only profile so Codex can start its sandbox helper.
    """
    entries = [f'{_toml(path)}="deny"' for path in policy.denied_read_paths]
    head = ""
    if policy.read_only:
        confined = ['":root"="deny"', '":minimal"="read"', '":workspace_roots"={"."="read"}']
        if install is not None:
            confined.append(f'{_toml(str(install))}="read"')
        entries = [*confined, *entries]
    else:
        head = 'extends=":workspace",'
    return f"{{{head}filesystem={{{','.join(entries)}}},network={{enabled=false}}}}"


def build_argv(
    codex_cmd: Sequence[str],
    policy: AgentPolicy,
    *,
    model: str | None = None,
    base_url: str | None = None,
) -> list[str]:
    """The full ``codex exec`` command line; the prompt comes from stdin (``-``)."""
    install = install_dir(codex_cmd[0]) if codex_cmd and Path(codex_cmd[0]).is_absolute() else None
    overrides = [
        'approval_policy="never"',
        f"default_permissions={_toml(PROFILE)}",
        f"permissions.{PROFILE}={permission_profile(policy, install)}",
        'web_search="disabled"',
        "features.apps=false",
        "features.plugins=false",
        "features.hooks=false",
        "features.multi_agent=false",
        "features.memories=false",
        # On by default in 0.166.0 and reaching outside the profile: browser, computer use,
        # plugin and dependency installs.
        *(f"features.{name}=false" for name in EXTRA_FEATURES_OFF),
        "allow_login_shell=false",
        # Drop variables named like KEY, SECRET or TOKEN from the agent's commands.
        "shell_environment_policy.ignore_default_excludes=false",
        'history.persistence="none"',
        "check_for_update_on_startup=false",
    ]
    if base_url is not None:
        provider = (
            f'{{name="SpoolHQ endpoint",base_url={_toml(base_url)},'
            f"env_key={_toml(token_var(BACKEND_NAME))}}}"
        )
        overrides += [f"model_provider={_toml(PROVIDER)}", f"model_providers.{PROVIDER}={provider}"]
    argv = [
        *codex_cmd,
        "exec",
        "--json",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        # An override this Codex doesn't know stops the run instead of being ignored.
        "--strict-config",
        "--cd",
        str(policy.worktree),
    ]
    if model is not None:
        argv += ["--model", model]
    for override in overrides:
        argv += ["-c", override]
    return [*argv, "-"]


def child_env(
    parent: Mapping[str, str], *, platform: str, endpoint_token: str | None = None
) -> dict[str, str]:
    """The only environment the ``codex`` process gets: the allowlist, Codex's own
    documented variables, ENV_SET and, with a custom endpoint, SpoolHQ's token under the
    name the provider's ``env_key`` gives."""
    env = allowed_env(parent, platform=platform, extra=ENV_EXTRA)
    env.update(ENV_SET)
    if endpoint_token is not None:
        env[token_var(BACKEND_NAME)] = endpoint_token
    return env
