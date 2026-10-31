"""The Codex CLI adapter: drives the user's own ``codex`` in ``codex exec --json`` mode.

As with Claude Code, SpoolHQ does not enforce the policy itself: it hands Codex a
per-run permission profile and overrides (``codex_config``), refuses up front any part
Codex can't enforce on this machine, and stops the run if the stream shows the
configuration didn't hold (``CodexStreamParser``). The prompt goes to stdin only; every
process call is an argument list. See ``docs/agents.md``.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
from collections.abc import Callable, Sequence
from pathlib import Path

from spoolhq.services.agents.claude_cli import format_version, parse_version
from spoolhq.services.agents.claude_config import check_worktree
from spoolhq.services.agents.codex_config import (
    BACKEND_NAME,
    build_argv,
    child_env,
    policy_parts,
    refusal,
    with_codex_home,
)
from spoolhq.services.agents.codex_stream import CodexStreamParser
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

MIN_VERSION = (0, 166, 0)
"""The version whose docs the flags and overrides were checked against."""
DETECT_TIMEOUT_S = 15.0
SYSTEM_CONFIG = Path("/etc/codex/config.toml")
INSTALL_HINT = (
    "Codex CLI is not installed; install it (https://learn.chatgpt.com/docs/codex/cli), "
    "then log in with: codex login"
)
LOGIN_HINT = "Codex CLI is not logged in; run: codex login"
LINUX_PACKAGES_REASON = (
    "Codex's sandbox needs bubblewrap on PATH; install it (Fedora: sudo dnf install "
    "bubblewrap; Debian/Ubuntu: sudo apt install bubblewrap)"
)
WINDOWS_REASON = (
    "Codex's deny rules for credential files depend on a Windows sandbox setup SpoolHQ "
    "can't check; run SpoolHQ inside WSL2 to use this backend"
)

Which = Callable[[str], str | None]


def login_method(text: str) -> str:
    """The method in ``codex login status``'s output (``Logged in using ChatGPT``)."""
    lowered = text.lower()
    if "chatgpt" in lowered:
        return "chatgpt"
    if "api key" in lowered:
        return "api_key"
    return "unknown"


def billing_for(method: str | None) -> Billing:
    if method == "chatgpt":
        return "subscription"
    if method == "api_key":
        return "api"
    return "unknown"


def legacy_sandbox(config: Path) -> str | None:
    """Why ``config`` (the system config) would switch the permission profile off: Codex
    uses the older sandbox settings when any loaded config sets them."""
    try:
        data = tomllib.loads(config.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        return f"cannot read {config} ({type(exc).__name__}), which may change Codex's sandbox"
    for key in ("sandbox_mode", "sandbox_workspace_write"):
        if key in data:
            return f"{config} sets {key}, which turns off the permission profile SpoolHQ uses"
    return None


class CodexCliRunner:
    """``AgentRunner`` for the ``codex`` CLI (Codex CLI 0.166.0 or newer).

    ``base_url`` and ``model`` come from ``agents.backends`` in ``project.yaml``: a custom
    endpoint becomes a per-run model provider with SpoolHQ's own token. ``codex_cmd``,
    ``platform``, ``which``, ``home`` and ``system_config`` are injectable for tests only.
    """

    name = BACKEND_NAME

    def __init__(
        self,
        codex_cmd: Sequence[str] | None = None,
        platform: str = sys.platform,
        which: Which = shutil.which,
        home: Path | None = None,
        system_config: Path = SYSTEM_CONFIG,
        *,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self._codex_cmd = tuple(codex_cmd) if codex_cmd is not None else None
        self._platform = platform
        self._which = which
        self._home = home if home is not None else Path.home()
        self._system_config = system_config

    # --- detection ------------------------------------------------------------------

    def _command(self) -> tuple[str, ...] | None:
        if self._codex_cmd is not None:
            return self._codex_cmd
        found = self._which("codex")
        return (found,) if found else None

    def _probe(self, argv: Sequence[str]) -> tuple[int, str] | None:
        try:
            with tempfile.TemporaryDirectory(
                prefix="spoolhq-codex-", ignore_cleanup_errors=True
            ) as cwd:
                completed = subprocess.run(  # noqa: S603 - fixed argument list, no shell
                    list(argv),
                    cwd=cwd,
                    env=self._env(),
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=DETECT_TIMEOUT_S,
                    check=False,
                )
        except (OSError, subprocess.SubprocessError):
            return None
        return completed.returncode, completed.stdout + completed.stderr

    def _sandbox_reason(self) -> tuple[str | None, bool]:
        """(why the OS sandbox can't run Codex's profile here, whether deny rules hold)."""
        if self._platform == "win32":
            return None, False
        if self._platform.startswith("linux"):
            if self._which("bwrap") is None:
                return LINUX_PACKAGES_REASON, True
        elif self._platform != "darwin":
            return f"Codex's sandbox is not available on {self._platform}", True
        return legacy_sandbox(self._system_config), True

    def detect(self) -> BackendInfo:
        """Whether ``codex`` is installed, logged in, and which policy parts it enforces."""
        cmd = self._command()
        probed = None if cmd is None else self._probe([*cmd, "--version"])
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

        method: str | None
        if self.base_url is not None:
            # A custom endpoint gets SpoolHQ's token, never the user's login.
            logged_in, method = self._token() is not None, "endpoint token"
            login_hint = missing_token(self.name, self.base_url)
        else:
            status = self._probe([*cmd, "login", "status"])
            logged_in = status is not None and status[0] == 0
            method = login_method(status[1]) if status is not None and logged_in else None
            login_hint = LOGIN_HINT

        parts: dict[str, dict[str, bool]] = {}
        reason: str | None
        if parsed is None or parsed < MIN_VERSION:
            reason = (
                f"Codex CLI {version} is too old; SpoolHQ needs "
                f"{format_version(MIN_VERSION)} or newer (run: codex update)"
            )
        else:
            reason, deny_rules = self._sandbox_reason()
            parts = policy_parts(sandbox=reason is None, denied_reads=deny_rules)
            if reason is None and not deny_rules:
                reason = WINDOWS_REASON
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
            policy_parts=parts,
        )

    def _token(self) -> str | None:
        return None if self.base_url is None else endpoint_token(self.name, self.base_url)

    def _env(self) -> dict[str, str]:
        # The real OS, not the injected platform: the process runs here.
        return child_env(os.environ, platform=sys.platform, endpoint_token=self._token())

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
        if cmd is None or not (info.installed and info.logged_in) or not info.policy_parts:
            raise BackendUnavailableError(info.reason or "Codex CLI is not available")
        refused = refusal(policy, info.policy_parts)
        if refused is not None:
            raise BackendUnavailableError(refused)
        env = self._env()
        policy = with_codex_home(policy, env, home=self._home, codex_exe=cmd[0])
        check_worktree(policy, self._home)
        model = model or self.model
        argv = build_argv(cmd, policy, model=model, base_url=self.base_url)
        parser = CodexStreamParser(
            policy.worktree,
            read_only=policy.read_only,
            model=model or "",
            backend_version=info.version or "",
        )
        session = Session(argv, policy.worktree, env, prompt, label="Codex CLI")
        try:
            return session.drive(parser, budget, on_event, on_raw, cancel)
        finally:
            session.close()
