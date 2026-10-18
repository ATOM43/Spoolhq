"""The Claude Code adapter: drives the user's own ``claude`` CLI in headless mode.

SpoolHQ does not enforce the policy itself; it builds Claude Code's configuration
(``build_argv``, ``sandbox_settings``, ``child_env``), checks that it took effect (the
``init`` message, through ``ClaudeStreamParser``) and stops the run if it didn't. The
four layers are described in ``docs/agents.md``. Every process call is an argument
list; the prompt goes to stdin only.
"""

import dataclasses
import json
import os
import queue
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import IO, Any

from spoolhq.services.agents.claude_stream import (
    BACKEND_NAME,
    CLAUDE_TOOLS,
    FILE_TOOLS,
    ClaudeStreamParser,
    PolicyViolation,
)
from spoolhq.services.agents.model import (
    AgentPolicy,
    BackendInfo,
    Billing,
    Budget,
    Outcome,
    PolicyError,
    RunResult,
)
from spoolhq.services.agents.runner import (
    BackendUnavailableError,
    EventCallback,
    RawCallback,
)

MIN_VERSION = (2, 1, 259)
DETECT_TIMEOUT_S = 15.0
STDERR_LINES = 50
MAX_PROMPT_BYTES = 10 * 1024 * 1024
POLL_S = 0.1
EXIT_WAIT_S = 10.0
INTERRUPT_WAIT_S = 10.0
TERMINATE_WAIT_S = 5.0

ENV_ALLOWED = frozenset(
    {
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "TMPDIR",
        "TMP",
        "TEMP",
        "XDG_CONFIG_HOME",
        "XDG_DATA_HOME",
        "XDG_CACHE_HOME",
        "XDG_RUNTIME_DIR",
        "DBUS_SESSION_BUS_ADDRESS",
        "CLAUDE_CONFIG_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "https_proxy",
        "http_proxy",
        "no_proxy",
        # A corporate proxy's CA, so Claude Code can reach the API through it.
        "NODE_EXTRA_CA_CERTS",
        "SSL_CERT_FILE",
    }
)
ENV_ALLOWED_WINDOWS = frozenset(
    {"SYSTEMROOT", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "COMSPEC", "PATHEXT"}
)
ENV_ALLOWED_PREFIXES = ("LC_",)
API_KEY_VAR = "ANTHROPIC_API_KEY"
ENV_SET = {
    # Claude Code removes its own credentials from the environment of the commands
    # the agent runs.
    "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB": "1",
    "DISABLE_AUTOUPDATER": "1",
}
# With CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1, Claude Code 2.1.302 reports (and uses) the
# "default" mode instead of dontAsk. With --permission-prompts none, every call that
# would prompt there is denied, as in dontAsk; any other mode stops the run.
PERMISSION_MODES = frozenset({"dontAsk", "default"})

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


def billing_for(auth_method: str | None) -> Billing:
    if auth_method in SUBSCRIPTION_METHODS:
        return "subscription"
    if auth_method in API_METHODS:
        return "api"
    return "unknown"


def child_env(parent: Mapping[str, str], *, billing: Billing, platform: str) -> dict[str, str]:
    """The only environment the ``claude`` process gets: an allowlist, plus ENV_SET.

    ``ANTHROPIC_API_KEY`` is passed only for API billing; with it, Claude Code would
    bill the API instead of the subscription.
    """
    windows = platform == "win32"
    allowed = ENV_ALLOWED | ENV_ALLOWED_WINDOWS if windows else ENV_ALLOWED
    if billing == "api":
        allowed = allowed | {API_KEY_VAR}
    env: dict[str, str] = {}
    for name, value in parent.items():
        key = name.upper() if windows else name  # Windows names ignore case
        if key in allowed or key.startswith(ENV_ALLOWED_PREFIXES):
            env[name] = value
    env.update(ENV_SET)
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
        ",".join(CLAUDE_TOOLS),
        "--allowedTools",
        *FILE_TOOLS,
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


class ClaudeCliRunner:
    """``AgentRunner`` for the ``claude`` CLI (Claude Code 2.1.259 or newer).

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
    ) -> None:
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

    def _platform_reason(self) -> str | None:
        if self._platform == "win32":
            return WINDOWS_REASON
        if self._platform.startswith("linux"):
            if self._which("bwrap") is None or self._which("socat") is None:
                return LINUX_PACKAGES_REASON
            return None
        if self._platform == "darwin":
            return None
        return f"Claude Code's Bash sandbox is not available on {self._platform}"

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
            reason = self._platform_reason()
        enforceable = reason is None
        if reason is None and not logged_in:
            reason = LOGIN_HINT
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

    def _env(self, billing: Billing) -> dict[str, str]:
        # The real OS, not the injected platform: the process runs here.
        return child_env(os.environ, billing=billing, platform=sys.platform)

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
        argv = build_argv(cmd, policy, budget, billing=info.billing, model=model)
        parser = ClaudeStreamParser(
            policy.worktree,
            billing=info.billing,
            permission_modes=PERMISSION_MODES,
            backend_version=info.version or "",
        )
        stubs = existing_stubs(policy.worktree)
        session = _Session(argv, policy.worktree, env, prompt)
        try:
            return session.drive(parser, budget, on_event, on_raw, cancel)
        finally:
            session.close()
            remove_new_stubs(policy.worktree, stubs)


class _Session:
    """One ``claude`` process: its pipes, reader threads and teardown."""

    def __init__(self, argv: list[str], cwd: Path, env: dict[str, str], prompt: str) -> None:
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.stderr: deque[str] = deque(maxlen=STDERR_LINES)
        options: dict[str, Any] = {}
        if sys.platform != "win32":
            # Its own process group, so stopping it reaches the commands it started.
            options["start_new_session"] = True
        self.proc = subprocess.Popen(  # noqa: S603 - fixed argument list, no shell
            argv,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            encoding="utf-8",
            errors="replace",
            **options,
        )
        self.threads = [
            threading.Thread(target=self._write, args=(prompt,), daemon=True),
            threading.Thread(target=self._read_stdout, daemon=True),
            threading.Thread(target=self._read_stderr, daemon=True),
        ]
        for thread in self.threads:
            thread.start()

    def _write(self, prompt: str) -> None:
        stdin = self.proc.stdin
        assert stdin is not None  # noqa: S101 - Popen(stdin=PIPE)
        try:
            stdin.write(prompt)
            stdin.close()
        except (OSError, ValueError):
            pass  # claude exited before reading it all; the run's result says why

    def _read_stdout(self) -> None:
        try:
            for line in _stream(self.proc.stdout):
                self.lines.put(line)
        except (OSError, ValueError):
            pass
        finally:
            self.lines.put(None)

    def _read_stderr(self) -> None:
        try:
            for line in _stream(self.proc.stderr):
                self.stderr.append(line.rstrip("\n"))
        except (OSError, ValueError):
            pass

    def drive(
        self,
        parser: ClaudeStreamParser,
        budget: Budget,
        on_event: EventCallback,
        on_raw: RawCallback | None,
        cancel: threading.Event,
    ) -> RunResult:
        deadline = time.monotonic() + budget.timeout_s
        stopped: tuple[Outcome, str | None] | None = None
        invalid_lines = 0
        while True:
            if cancel.is_set():
                stopped = (Outcome.CANCELLED, None)
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                stopped = (Outcome.TIMED_OUT, None)
                break
            try:
                line = self.lines.get(timeout=min(POLL_S, remaining))
            except queue.Empty:
                continue
            if line is None:
                break
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError:
                message = None
            if not isinstance(message, dict):
                invalid_lines += 1
                continue
            if on_raw is not None:
                on_raw(message)
            try:
                events = parser.feed(message)
            except PolicyViolation as exc:
                stopped = (Outcome.ERROR, f"policy not enforced: {exc}")
                break
            for event in events:
                on_event(event)
            if budget.max_tokens is not None and parser.total_tokens > budget.max_tokens:
                stopped = (Outcome.BUDGET_EXHAUSTED, None)
                break

        if stopped is not None:
            self.stop()
            result = parser.finish(*stopped)
        else:
            try:
                self.proc.wait(timeout=max(POLL_S, min(EXIT_WAIT_S, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                self.stop()
            result = parser.finish()
        for thread in self.threads[1:]:
            thread.join(timeout=TERMINATE_WAIT_S)
        if result.outcome is Outcome.ERROR:
            result = replace(result, error=self._error_detail(result.error, parser.has_result))
        if invalid_lines:
            result = replace(result, debug={**result.debug, "invalid_lines": invalid_lines})
        return result

    def _error_detail(self, error: str | None, has_result: bool) -> str:
        parts = [error or "Claude Code failed"]
        if not has_result and self.proc.returncode is not None:
            parts[0] += f" (exit {self.proc.returncode})"
        if self.stderr:
            parts.append("\n".join(self.stderr))
        return "\n".join(parts)

    def stop(self) -> None:
        """SIGINT, then SIGTERM, then kill (``terminate`` then ``kill`` on Windows)."""
        proc = self.proc
        if proc.poll() is not None:
            return
        if sys.platform != "win32":
            steps = ((signal.SIGINT, INTERRUPT_WAIT_S), (signal.SIGTERM, TERMINATE_WAIT_S))
            for sig, wait in steps:
                _signal_group(proc.pid, sig)
                try:
                    proc.wait(timeout=wait)
                    return
                except subprocess.TimeoutExpired:
                    continue
            _signal_group(proc.pid, signal.SIGKILL)
        else:
            proc.terminate()
            try:
                proc.wait(timeout=TERMINATE_WAIT_S)
                return
            except subprocess.TimeoutExpired:
                proc.kill()
        proc.wait()

    def close(self) -> None:
        """Always run: no process left behind, every pipe closed."""
        try:
            self.stop()
        finally:
            if sys.platform != "win32":
                # Anything the agent left running in claude's process group.
                _signal_group(self.proc.pid, signal.SIGKILL)
            pipes = (self.proc.stdin, self.proc.stdout, self.proc.stderr)
            for thread, pipe in zip(self.threads, pipes, strict=True):
                thread.join(timeout=TERMINATE_WAIT_S)
                # Closing a pipe another thread is still reading or writing would wait
                # on that thread; it only stays open if something outside the process
                # group still holds the other end.
                if pipe is not None and not thread.is_alive():
                    try:
                        pipe.close()
                    except OSError:
                        pass


def _stream(pipe: IO[str] | None) -> Any:
    return iter(pipe.readline, "") if pipe is not None else iter(())


if sys.platform != "win32":

    def _signal_group(pid: int, sig: int) -> None:
        try:
            os.killpg(pid, sig)
        except (ProcessLookupError, PermissionError):
            pass

else:

    def _signal_group(pid: int, sig: int) -> None:
        raise NotImplementedError("process groups are POSIX only")
