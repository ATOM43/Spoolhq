"""Codex CLI's configuration for one run: the command line, the permission profile, the
environment, and which policy parts Codex can enforce.

Everything goes through ``codex exec`` flags and ``-c key=value`` overrides; the user's
``~/.codex/config.toml`` is not loaded (``--ignore-user-config``) and nothing is written
to it. Checked against the Codex CLI 0.166.0 docs; see ``docs/agents.md`` and DECISIONS.
"""

import dataclasses
import json
from collections.abc import Mapping, Sequence

from spoolhq.core.agent_policy import allowed_env
from spoolhq.services.agents.endpoint import token_var
from spoolhq.services.agents.model import AgentPolicy

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


def refusal(policy: AgentPolicy, parts: Mapping[str, Mapping[str, bool]]) -> str | None:
    """Why ``policy`` can't run on Codex here, naming the first part it can't enforce."""
    enforced = parts.get(policy.role, {})
    for part in required_parts(policy.read_only):
        if not enforced.get(part, False):
            return (
                f"backend '{BACKEND_NAME}' can't enforce {part}; "
                f"choose another backend for the {policy.role} role"
            )
    return None


def with_codex_home(policy: AgentPolicy, env: Mapping[str, str]) -> AgentPolicy:
    """``policy`` that also denies Codex's own folder (``~/.codex`` and ``CODEX_HOME``)."""
    extra = [*CODEX_PATHS, *filter(None, [env.get("CODEX_HOME")])]
    denied = [path for path in extra if path not in policy.denied_read_paths]
    return dataclasses.replace(policy, denied_read_paths=(*policy.denied_read_paths, *denied))


def _toml(value: str) -> str:
    # A JSON string is a valid TOML basic string.
    return json.dumps(value, ensure_ascii=False)


def permission_profile(policy: AgentPolicy) -> str:
    """The profile as a TOML inline table, for ``-c permissions.spoolhq=…``.

    Writing: Codex's ``:workspace`` (writes to the workspace roots and temp folders, the
    worktree's ``.git`` read-only). Read-only: no writes, and reads only in the worktree
    and Codex's ``:minimal`` runtime paths. Both: every denied path ``deny`` (no reads,
    no writes) and no network for the agent's commands.
    """
    entries = [f'{_toml(path)}="deny"' for path in policy.denied_read_paths]
    head = ""
    if policy.read_only:
        confined = ['":root"="deny"', '":minimal"="read"', '":workspace_roots"={"."="read"}']
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
    overrides = [
        'approval_policy="never"',
        f"default_permissions={_toml(PROFILE)}",
        f"permissions.{PROFILE}={permission_profile(policy)}",
        'web_search="disabled"',
        "features.apps=false",
        "features.plugins=false",
        "features.hooks=false",
        "features.multi_agent=false",
        "features.memories=false",
        "tools.view_image=false",
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
