"""The Claude Agent SDK backend (``claude-agent-sdk``), for users with an Anthropic API key.

The SDK drives the Claude Code CLI it bundles. SpoolHQ starts that CLI with the same
policy layers as the ``claude-code-cli`` adapter (``claude_config``: restricted mode, the
allowlist, the OS sandbox, a scrubbed environment), plus ``--bare`` and no setting
sources, so neither a stored claude.ai login nor the user's ``~/.claude`` settings and
hooks are read. On top, a ``PreToolUse`` hook (``check_tool``) checks every tool call on
its parsed arguments and denies what the role may not do. The key comes from
``ANTHROPIC_API_KEY`` or the keychain and goes only into that process's environment.
See ``docs/agents.md``.
"""

import logging
import os
import shlex
import shutil
import sys
import tempfile
import threading
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import claude_agent_sdk
import keyring
from claude_agent_sdk import ClaudeAgentOptions, HookContext, HookInput, HookJSONOutput, HookMatcher
from keyring.errors import KeyringError

from spoolhq.services.agents.agent_sdk_stream import CliTransport, SdkRun
from spoolhq.services.agents.claude_cli import (
    MAX_PROMPT_BYTES,
    MIN_VERSION,
    format_version,
    parse_version,
    platform_reason,
    probe,
)
from spoolhq.services.agents.claude_config import (
    API_KEY_VAR,
    build_argv,
    check_worktree,
    child_env,
    existing_stubs,
    expand_home,
    permission_modes,
    remove_new_stubs,
    requested_tools,
    with_config_dir,
)
from spoolhq.services.agents.claude_stream import ClaudeStreamParser
from spoolhq.services.agents.codex_config import ROLES, refusal, required_parts
from spoolhq.services.agents.endpoint import KEYRING_SERVICE, endpoint_token, missing_token
from spoolhq.services.agents.model import (
    FORBIDDEN_COMMAND_CHARS,
    AgentPolicy,
    BackendInfo,
    Budget,
    RunResult,
)
from spoolhq.services.agents.runner import BackendUnavailableError, EventCallback, RawCallback

logger = logging.getLogger(__name__)

BACKEND_NAME = "claude-agent-sdk"
CONFIG_DIR_VAR = "CLAUDE_CONFIG_DIR"
KEYRING_KEY = "anthropic"
MISSING_KEY = f"backend '{BACKEND_NAME}' needs an API key; run spool secrets set {KEYRING_KEY}"
NO_CLI = (
    "the Agent SDK's bundled Claude Code is missing and no claude is on PATH; reinstall spoolhq"
)
SDK_ENV = {
    # What the SDK's own transport sets: identifies the client, and lets the CLI report
    # its session state so the SDK knows when the run has ended.
    "CLAUDE_CODE_ENTRYPOINT": "sdk-py",
    "CLAUDE_AGENT_SDK_VERSION": claude_agent_sdk.__version__,
    "CLAUDE_AGENT_SDK_CLIENT_APP": "spoolhq",
    "CLAUDE_CODE_SDK_READS_SESSION_STATE": "1",
}
SDK_FLAGS = (
    # The SDK's setting_sources=[]: no user, project or local settings files.
    "--setting-sources=",
    "--input-format",
    "stream-json",
)
PATH_KEYS = {
    "Read": "file_path",
    "Edit": "file_path",
    "Write": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
    "Glob": "path",
    "Grep": "path",
}

Which = Callable[[str], str | None]
Denied = Callable[[str, str, Any, str], None]


# --- the API key ----------------------------------------------------------------------


def api_key() -> tuple[str, str] | None:
    """(key, where it came from): ``ANTHROPIC_API_KEY``, else the keychain; None without."""
    key = os.environ.get(API_KEY_VAR, "").strip()
    if key:
        return key, "environment"
    try:
        stored = keyring.get_password(KEYRING_SERVICE, KEYRING_KEY)
    except (KeyringError, RuntimeError) as exc:
        logger.warning("cannot read the OS keychain", extra={"error": type(exc).__name__})
        return None
    stored = (stored or "").strip()
    return (stored, "keychain") if stored else None


def store_api_key(key: str) -> None:
    """Save ``key`` in the OS keychain; KeyringError if there is no usable keychain."""
    if not key.strip():
        raise ValueError("the API key is empty")
    keyring.set_password(KEYRING_SERVICE, KEYRING_KEY, key.strip())


# --- the policy hook ------------------------------------------------------------------


def check_tool(policy: AgentPolicy, home: Path, name: str, tool_input: Any) -> str | None:
    """Why the agent under ``policy`` may not make this tool call, or None if it may.

    File tools must stay inside the worktree and off the denied paths (reads too);
    Bash runs only an allowlisted command, checked on its parsed argument list. Anything
    else (web, MCP, subagents) is refused.
    """
    if name not in requested_tools(policy):
        return f"{name} is not allowed for the {policy.role}"
    if not isinstance(tool_input, Mapping):
        return "the tool input is not an object"
    if name == "Bash":
        if tool_input.get("dangerouslyDisableSandbox"):
            return "commands may not leave the sandbox"
        return check_command(policy, tool_input.get("command"))
    if name == "Glob":
        pattern = tool_input.get("pattern")
        if not isinstance(pattern, str) or not relative_pattern(pattern):
            return f"glob pattern {pattern!r} must be relative, without '..'"
    raw = tool_input.get(PATH_KEYS[name], ".")  # Glob and Grep search the worktree by default
    if not isinstance(raw, str) or not raw:
        return "the path is missing"
    return check_path(policy, home, raw)


def relative_pattern(pattern: str) -> bool:
    parts = pattern.replace("\\", "/").split("/")
    return (
        bool(pattern)
        and not pattern.startswith(("/", "~"))
        and ":" not in parts[0]
        and (".." not in parts)
    )


def check_path(policy: AgentPolicy, home: Path, raw: str) -> str | None:
    """Why ``raw`` (absolute, ``~/…`` or relative to the worktree) is out of bounds."""
    if raw.startswith("~") and not raw.startswith("~/"):
        return f"{raw} is outside the worktree"
    path = expand_home(raw, home)
    path = (path if path.is_absolute() else policy.worktree / path).resolve()
    for denied in policy.denied_read_paths:
        target = expand_home(denied, home).resolve()
        if path == target or target in path.parents:
            return f"{raw} is under {denied}, which agents may not read"
    worktree = policy.worktree.resolve()
    if path != worktree and worktree not in path.parents:
        return f"{raw} is outside the worktree"
    return None


def check_command(policy: AgentPolicy, command: Any) -> str | None:
    """Why ``command`` isn't one of the policy's commands (plus arguments), or None."""
    if not isinstance(command, str) or not command.strip():
        return "the command is empty"
    if any(char in FORBIDDEN_COMMAND_CHARS for char in command):
        return f"{command!r} contains shell operators or wildcards"
    try:
        argv = shlex.split(command)
    except ValueError:
        return f"{command!r} cannot be parsed"
    for allowed in policy.commands:
        prefix = shlex.split(allowed)
        if argv[: len(prefix)] == prefix:
            if prefix[0] == "git" and any(arg.startswith("--output") for arg in argv):
                return f"{command!r} would write a file"
            return None
    return f"{command!r} is not on the allowlist: {', '.join(policy.commands) or 'nothing'}"


def make_hook(policy: AgentPolicy, home: Path, on_denied: Denied) -> HookMatcher:
    """The ``PreToolUse`` hook for every tool. A denial is reported through
    ``on_denied``; an allowed call still goes through Claude Code's own rules."""

    async def pre_tool_use(
        hook_input: HookInput, tool_use_id: str | None, context: HookContext
    ) -> HookJSONOutput:
        data: Mapping[str, Any] = hook_input
        name = str(data.get("tool_name", ""))
        tool_input = data.get("tool_input")
        try:
            reason = check_tool(policy, home, name, tool_input)
        except Exception as exc:  # noqa: BLE001 - fail closed
            reason = f"the policy check failed ({type(exc).__name__})"
        if reason is None:
            return {}
        on_denied(name, tool_use_id or "", tool_input, reason)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }

    return HookMatcher(matcher=None, hooks=[pre_tool_use])


def policy_parts(sandbox: bool) -> dict[str, dict[str, bool]]:
    """Role -> part -> enforced. Every part needs Claude Code's OS sandbox, which
    ``failIfUnavailable`` requires before anything runs; approvals are never asked."""
    return {
        role: {part: sandbox for part in required_parts(role != "implementer")} for role in ROLES
    }


# --- the runner -----------------------------------------------------------------------


class AgentSdkRunner:
    """``AgentRunner`` on the Claude Agent SDK and the Claude Code CLI it bundles.

    ``base_url`` and ``model`` come from ``agents.backends`` in ``project.yaml``; with a
    ``base_url`` the endpoint gets SpoolHQ's endpoint token instead of the API key.
    ``cli_cmd`` (the CLI's command, the bundled one by default), ``platform``, ``which``
    and ``home`` are injectable for tests.
    """

    name = BACKEND_NAME

    def __init__(
        self,
        cli_cmd: Sequence[str] | None = None,
        platform: str = sys.platform,
        which: Which = shutil.which,
        home: Path | None = None,
        *,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._cli_cmd = tuple(cli_cmd) if cli_cmd is not None else None
        self._platform = platform
        self._which = which
        self._home = home if home is not None else Path.home()

    def _cli(self) -> tuple[str, ...] | None:
        """The CLI the SDK would start: its bundled one, else ``claude`` on PATH."""
        if self._cli_cmd is not None:
            return self._cli_cmd
        bundled = Path(claude_agent_sdk.__file__).parent / "_bundled"
        for name in ("claude.exe", "claude") if sys.platform == "win32" else ("claude",):
            if (bundled / name).is_file():
                return (str(bundled / name),)
        found = self._which("claude")
        return (found,) if found else None

    def _credential(self) -> tuple[str, str] | None:
        """(secret, auth method): the endpoint token with a ``base_url``, else the key."""
        if self.base_url is not None:
            token = endpoint_token(self.name, self.base_url)
            return (token, "endpoint token") if token else None
        found = api_key()
        return (found[0], f"api key from {found[1]}") if found else None

    def _env(self, secret: str | None, config_dir: str | None = None) -> dict[str, str]:
        endpoint = secret if self.base_url is not None else None
        env = child_env(
            os.environ,
            billing="unknown",  # the parent's own ANTHROPIC_API_KEY never passes as is
            platform=sys.platform,
            base_url=self.base_url,
            endpoint_token=endpoint,
        )
        env.update(SDK_ENV)
        if config_dir is not None:
            env[CONFIG_DIR_VAR] = config_dir
        if self.base_url is None and secret is not None:
            env[API_KEY_VAR] = secret
        return env

    def detect(self) -> BackendInfo:
        """The SDK and CLI versions, whether a key is set (never the key) and the policy
        parts per role."""
        cli = self._cli()
        probed = None if cli is None else probe([*cli, "--version"], self._env(None))
        sdk = claude_agent_sdk.__version__
        if cli is None or probed is None or probed[0] != 0:
            return BackendInfo(
                name=self.name,
                installed=False,
                version=sdk,
                logged_in=False,
                auth_method=None,
                billing="unknown",
                policy_enforceable=False,
                reason=NO_CLI,
            )
        where = "bundled" if Path(cli[0]).parent.name == "_bundled" else "PATH"
        parsed = parse_version(probed[1])
        cli_version = format_version(parsed) if parsed else probed[1].strip()
        reason: str | None
        if parsed is None or parsed < MIN_VERSION:
            reason = (
                f"Claude Code {cli_version} is too old; SpoolHQ needs "
                f"{format_version(MIN_VERSION)} or newer"
            )
        else:
            reason = platform_reason(self._platform, self._which)
        enforceable = reason is None
        credential = self._credential()
        if reason is None and credential is None:
            reason = (
                MISSING_KEY if self.base_url is None else missing_token(self.name, self.base_url)
            )
        return BackendInfo(
            name=self.name,
            installed=True,
            version=f"{sdk}, {where} Claude Code {cli_version}",
            logged_in=credential is not None,
            auth_method=credential[1] if credential else None,
            billing="api" if credential and self.base_url is None else "unknown",
            policy_enforceable=enforceable,
            reason=reason,
            policy_parts=policy_parts(enforceable),
        )

    def run(
        self,
        prompt: str,
        policy: AgentPolicy,
        budget: Budget,
        *,
        model: str | None = None,
        on_event: EventCallback,
        on_raw: RawCallback | None = None,
        cancel: threading.Event,
    ) -> RunResult:
        info = self.detect()
        cli, credential = self._cli(), self._credential()
        if not info.usable or cli is None or credential is None:
            raise BackendUnavailableError(info.reason or MISSING_KEY)
        refused = refusal(policy, info.policy_parts, self.name)
        if refused is not None:
            raise BackendUnavailableError(refused)
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("the prompt is larger than Claude Code's 10 MB limit")
        # An empty, per-run config folder: no stored claude.ai login (its credentials live
        # there), none of the user's settings, hooks or MCP servers, and nothing written
        # to ~/.claude. with_config_dir denies it to the agent's commands.
        with tempfile.TemporaryDirectory(
            prefix="spoolhq-sdk-", ignore_cleanup_errors=True
        ) as config_dir:
            env = self._env(credential[0], config_dir)
            return self._run(
                cli, info, prompt, policy, budget, env, model, on_event, on_raw, cancel
            )

    def _run(
        self,
        cli: tuple[str, ...],
        info: BackendInfo,
        prompt: str,
        policy: AgentPolicy,
        budget: Budget,
        env: dict[str, str],
        model: str | None,
        on_event: EventCallback,
        on_raw: RawCallback | None,
        cancel: threading.Event,
    ) -> RunResult:
        policy = with_config_dir(policy, env)
        check_worktree(policy, self._home)
        argv = [
            *build_argv(cli, policy, budget, billing=info.billing, model=model or self.model),
            *SDK_FLAGS,
        ]
        parser = ClaudeStreamParser(
            policy.worktree,
            billing=info.billing,
            requested_tools=requested_tools(policy),
            exact_tools=policy.read_only,
            permission_modes=permission_modes(env, argv),
            backend=self.name,
            backend_version=info.version or "",
        )
        stubs = existing_stubs(policy.worktree)
        transport = CliTransport(argv, policy.worktree, env)
        # With the API key, init must name it as the credential (checked against 2.1.316).
        key_source = API_KEY_VAR if self.base_url is None else None
        sdk_run = SdkRun(transport, parser, budget, on_event, on_raw, cancel, key_source)
        hook = make_hook(policy, self._home, sdk_run.deny)
        try:
            return sdk_run.run(prompt, ClaudeAgentOptions(hooks={"PreToolUse": [hook]}))
        finally:
            remove_new_stubs(policy.worktree, stubs)
