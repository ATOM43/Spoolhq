"""Running Graphify: finding it, reading its version, and one command with a timeout.

Graphify is an external tool (``graphifyy`` on PyPI), never a dependency. It runs offline:
``GRAPHIFY_BACKEND=none``, an allowlisted environment (no API keys), argument lists only.
"""

import os
import re
import shutil
import signal
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from spoolhq.core.agent_policy import allowed_env

TESTED_VERSION = "0.9.92"
TIMEOUT_S = 120.0
VERSION_TIMEOUT_S = 30.0
ENV_SET = {"GRAPHIFY_BACKEND": "none"}
_VERSION_RE = re.compile(r"graphify (\d+(?:\.\d+)+)")
_ERROR_CHARS = 500


class GraphifyError(Exception):
    """A Graphify command failed, timed out or could not start."""


@dataclass(frozen=True)
class Graphify:
    command: tuple[str, ...]
    version: str

    @property
    def tested(self) -> bool:
        return self.version == TESTED_VERSION


def find_command(which: Callable[[str], str | None] = shutil.which) -> list[str] | None:
    """The command that starts Graphify, or None when it is not on PATH."""
    path = which("graphify")
    return [path] if path else None


def probe() -> Graphify | None:
    """Graphify and its version; None when it is missing or its version can't be read."""
    command = find_command()
    if not command:
        return None
    try:
        output = run(command, ["--version"], cwd=None, timeout=VERSION_TIMEOUT_S)
    except GraphifyError:
        return None
    match = _VERSION_RE.search(output)
    return Graphify(tuple(command), match[1]) if match else None


def run(command: Sequence[str], args: Sequence[str], *, cwd: Path | None, timeout: float) -> str:
    """Run ``command args``; its stdout and stderr. GraphifyError on failure or timeout,
    after stopping the whole process tree (Graphify starts AST worker processes)."""
    env = allowed_env(os.environ, platform=sys.platform) | ENV_SET
    try:
        proc = subprocess.Popen(  # noqa: S603 - an argument list, no shell
            [*command, *args],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=sys.platform != "win32",
        )
    except OSError as exc:
        raise GraphifyError(f"cannot start graphify: {exc}") from exc
    try:
        out, _ = proc.communicate(timeout=max(timeout, 1.0))
    except subprocess.TimeoutExpired:
        _kill_tree(proc)
        proc.communicate()
        raise GraphifyError(f"graphify {args[0]} timed out after {timeout:.0f} s") from None
    text = out.decode("utf-8", errors="replace")
    if proc.returncode != 0:
        tail = text.strip()[-_ERROR_CHARS:]
        raise GraphifyError(f"graphify {args[0]} exited with code {proc.returncode}: {tail}")
    return text


def _kill_tree(proc: "subprocess.Popen[bytes]") -> None:
    if sys.platform == "win32":
        subprocess.run(  # noqa: S603 - a fixed argument list
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],  # noqa: S607 - a Windows system tool
            capture_output=True,
            check=False,
        )
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
    proc.kill()
