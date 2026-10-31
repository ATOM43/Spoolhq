"""The Claude Code adapter: drives the user's own ``claude`` CLI in headless mode.

SpoolHQ does not enforce the policy itself; it builds Claude Code's configuration
(``claude_config``: ``build_argv``, ``sandbox_settings``, ``child_env``), checks that it
took effect (the ``init`` message, through ``ClaudeStreamParser``) and stops the run if
it didn't. The four layers are described in ``docs/agents.md``. Every process call is
an argument list; the prompt goes to stdin only.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from spoolhq.services.agents.claude_config import (
    API_KEY_VAR,
    build_argv,
    check_worktree,
    child_env,
    existing_stubs,
    permission_modes,
    remove_new_stubs,
    requested_tools,
    with_config_dir,
)
from spoolhq.services.agents.claude_stream import BACKEND_NAME, ClaudeStreamParser
from spoolhq.services.agents.endpoint import endpoint_token, missing_token
from spoolhq.services.agents.model import (
    AgentPolicy,
    BackendInfo,
    Billing,
    Budget,
    RunResult,
)
from spoolhq.services.agents.process import Session
from spoolhq.services.agents.runner import (
    BackendUnavailableError,
    EventCallback,
    RawCallback,
)

MIN_VERSION = (2, 1, 259)
DETECT_TIMEOUT_S = 15.0
MAX_PROMPT_BYTES = 10 * 1024 * 1024

SUBSCRIPTION_METHODS = frozenset({"claude.ai", "oauth_token"})
API_METHODS = frozenset({"api_key", "api_key_helper"})
INSTALL_HINT = (
    "Claude Code is not installed; install it (https://code.claude.com/docs/en/setup), "
    "then log in with: claude auth login"
)
LOGIN_HINT = "Claude Code is not logged in; run: claude auth login"
WINDOWS_REASON = (
    "Claude Code's Bash sandbox is not available on native Windows; "
    "run SpoolHQ inside WSL2 to use this backend"
)
LINUX_PACKAGES_REASON = (
    "Claude Code's Bash sandbox needs bubblewrap and socat; install them "
    "(Fedora: sudo dnf install bubblewrap socat; Debian/Ubuntu: sudo apt install "
    "bubblewrap socat)"
)
_VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")

Which = Callable[[str], str | None]


def format_version(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


def parse_version(text: str) -> tuple[int, int, int] | None:
    match = _VERSION_RE.search(text)
    if match is None:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch)


def probe(argv: Sequence[str], env: Mapping[str, str]) -> tuple[int, str] | None:
    """``argv``'s exit code and stdout, in a throwaway folder; None if it can't run."""
    # In a throwaway folder: `claude auth status` leaves scrub stubs in its cwd.
    try:
        with tempfile.TemporaryDirectory(
            prefix="spoolhq-claude-", ignore_cleanup_errors=True
        ) as cwd:
            completed = subprocess.run(  # noqa: S603 - fixed argument list, no shell
                list(argv),
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                timeout=DETECT_TIMEOUT_S,
                check=False,
            )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.returncode, completed.stdout


def platform_reason(platform: str, which: Which) -> str | None:
    """Why Claude Code's Bash sandbox can't run on ``platform``, or None."""
    if platform == "win32":
        return WINDOWS_REASON
    if platform.startswith("linux"):
        if which("bwrap") is None or which("socat") is None:
            return LINUX_PACKAGES_REASON
        return None
    if platform == "darwin":
        return None
    return f"Claude Code's Bash sandbox is not available on {platform}"


def billing_for(auth_method: str | None) -> Billing:
    if auth_method in SUBSCRIPTION_METHODS:
        return "subscription"
    if auth_method in API_METHODS:
        return "api"
    return "unknown"


class ClaudeCliRunner:
    """``AgentRunner`` for the ``claude`` CLI (Claude Code 2.1.259 or newer).

    ``base_url`` (a custom endpoint, as ``ANTHROPIC_BASE_URL`` in the child's
    environment) and ``model`` (``--model``, unless ``run`` is given one) come from
    ``agents.backends`` in ``project.yaml``; neither touches the user's own config.
    ``claude_cmd``, ``platform``, ``which`` and ``home`` (the user's home folder) are
    injectable for tests only. ``platform`` decides the sandbox rules ``detect``
    applies; the environment and process handling always follow the real OS.
    """

    name = BACKEND_NAME

    def __init__(
        self,
        claude_cmd: Sequence[str] | None = None,
        platform: str = sys.platform,
        which: Which = shutil.which,
        home: Path | None = None,
        *,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._claude_cmd = tuple(claude_cmd) if claude_cmd is not None else None
        self._platform = platform
        self._which = which
        self._home = home if home is not None else Path.home()

    # --- detection ------------------------------------------------------------------

    def _command(self) -> tuple[str, ...] | None:
        if self._claude_cmd is not None:
            return self._claude_cmd
        found = self._which("claude")
        return (found,) if found else None

    def _probe(self, argv: Sequence[str], env: Mapping[str, str]) -> tuple[int, str] | None:
        return probe(argv, env)

    def _auth_status(self, cmd: Sequence[str], env: Mapping[str, str]) -> tuple[bool, str | None]:
        probed = self._probe([*cmd, "auth", "status"], env)
        if probed is None:
            return False, None
        returncode, stdout = probed
        try:
            data = json.loads(stdout)
        except ValueError:
            data = {}
        if not isinstance(data, dict):
            data = {}
        method = data.get("authMethod")
        method = method if isinstance(method, str) else None
        logged_in = returncode == 0 and data.get("loggedIn", True) is not False
        return logged_in and method != "none", method

    def detect(self) -> BackendInfo:
        """Whether ``claude`` is installed, logged in and can enforce the policy."""
        cmd = self._command()
        probed = None if cmd is None else self._probe([*cmd, "--version"], self._env("unknown"))
        if cmd is None or probed is None or probed[0] != 0:
            return BackendInfo(
                name=self.name,
                installed=False,
                version=None,
                logged_in=False,
                auth_method=None,
                billing="unknown",
                policy_enforceable=False,
                reason=INSTALL_HINT,
            )
        parsed = parse_version(probed[1])
        version = format_version(parsed) if parsed else probed[1].strip() or None

        login_hint = LOGIN_HINT
        method: str | None
        if self.base_url is not None:
            # A custom endpoint gets SpoolHQ's token, never the user's login.
            logged_in, method = self._token() is not None, "endpoint token"
            login_hint = missing_token(self.name, self.base_url)
        else:
            # A subscription login wins; ANTHROPIC_API_KEY is only offered if there is none.
            logged_in, method = self._auth_status(cmd, self._env("subscription"))
            if not logged_in and os.environ.get(API_KEY_VAR):
                logged_in, method = self._auth_status(cmd, self._env("api"))

        reason: str | None
        if parsed is None:
            reason = (
                f"cannot read Claude Code's version from {version!r}; SpoolHQ needs "
                f"{format_version(MIN_VERSION)} or newer (run: claude update)"
            )
        elif parsed < MIN_VERSION:
            reason = (
                f"Claude Code {version} is too old; SpoolHQ needs "
                f"{format_version(MIN_VERSION)} or newer (run: claude update)"
            )
        else:
            reason = platform_reason(self._platform, self._which)
        enforceable = reason is None
        if reason is None and not logged_in:
            reason = login_hint
        return BackendInfo(
            name=self.name,
            installed=True,
            version=version,
            logged_in=logged_in,
            auth_method=method,
            billing=billing_for(method) if logged_in else "unknown",
            policy_enforceable=enforceable,
            reason=reason,
        )

    def _token(self) -> str | None:
        return None if self.base_url is None else endpoint_token(self.name, self.base_url)

    def _env(self, billing: Billing) -> dict[str, str]:
        # The real OS, not the injected platform: the process runs here.
        return child_env(
            os.environ,
            billing=billing,
            platform=sys.platform,
            base_url=self.base_url,
            endpoint_token=self._token(),
        )

    # --- running --------------------------------------------------------------------

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
        cmd = self._command()
        if not info.usable or cmd is None:
            raise BackendUnavailableError(info.reason or "Claude Code is not available")
        env = self._env(info.billing)
        policy = with_config_dir(policy, env)
        check_worktree(policy, self._home)
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise ValueError("the prompt is larger than Claude Code's 10 MB stdin limit")
        argv = build_argv(cmd, policy, budget, billing=info.billing, model=model or self.model)
        parser = ClaudeStreamParser(
            policy.worktree,
            billing=info.billing,
            requested_tools=requested_tools(policy),
            exact_tools=policy.read_only,
            permission_modes=permission_modes(env, argv),
            backend_version=info.version or "",
        )
        stubs = existing_stubs(policy.worktree)
        session = Session(argv, policy.worktree, env, prompt)
        try:
            return session.drive(parser, budget, on_event, on_raw, cancel)
        finally:
            session.close()
            remove_new_stubs(policy.worktree, stubs)
