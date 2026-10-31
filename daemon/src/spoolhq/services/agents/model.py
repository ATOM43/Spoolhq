"""The agent policy, budget, events and results shared by every backend.

Everything here is a frozen value: a runner gets an ``AgentPolicy`` and a ``Budget``,
reports ``AgentEvent``s while it works and returns a ``RunResult``. See
``docs/agents.md``.
"""

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Literal

from spoolhq.core.agent_policy import READ_ONLY_GIT
from spoolhq.core.auth import token_path
from spoolhq.core.tokens import weighted_tokens

CREDENTIAL_PATHS: tuple[str, ...] = (
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
    # Claude Code's own login, settings and other projects' transcripts. Only the
    # agent's commands are denied them; the claude process itself still reads them.
    "~/.claude",
    "~/.claude.json",
)
"""Files the sandbox never lets an agent's commands read; the SpoolHQ home is added."""

# Characters that would let one allowlisted command become several, redirect output,
# expand variables or match more than the command itself in a permission rule.
FORBIDDEN_COMMAND_CHARS = frozenset(";&|<>$`()*?[]{}\\\n\r")

Billing = Literal["subscription", "api", "unknown"]


class PolicyError(ValueError):
    """The policy cannot be built: a stack command or the worktree is not acceptable."""


def check_command(field_name: str, command: str) -> str:
    """Return ``command`` if it is safe to turn into permission rules, else raise."""
    if not command.strip():
        raise PolicyError(f"{field_name}: must not be empty")
    if any(char in FORBIDDEN_COMMAND_CHARS for char in command):
        raise PolicyError(
            f"{field_name}: {command!r} contains shell operators or wildcards; use a plain command"
        )
    if command != command.strip():
        raise PolicyError(
            f"{field_name}: {command!r} has leading or trailing spaces; use a plain command"
        )
    return command


def home_denials(home: Path, worktree: Path) -> tuple[str, ...]:
    """The SpoolHQ home paths the sandbox denies reads of.

    Normally the home folder itself. Worktrees live inside it by default
    (``<home>/worktrees/<project>/<ticket>``), and denying the whole folder would deny
    the worktree too; then it is the token file plus everything in the home except
    the folders on the way down to the worktree.
    """
    home, worktree = home.resolve(), worktree.resolve()
    if not worktree.is_relative_to(home):
        return (str(home),)
    return tuple(dict.fromkeys((str(token_path(home)), *denials_except(home, worktree))))


def denials_except(folder: Path, keep: Path) -> tuple[str, ...]:
    """Everything in ``folder`` except the folders on the way down to ``keep`` (which
    must be inside it), so a sandbox can deny the rest while ``keep`` stays reachable.

    shortcut: entries created after the run starts aren't denied; fine while the
    folders it is used on only gain files the agent may see, revisit otherwise.
    """
    denied: list[str] = []
    current = folder
    for part in keep.relative_to(folder).parts:
        if current.is_dir():
            # bwrap can't mount over a symlink; its target is denied (or not) on its own.
            denied += [
                str(entry)
                for entry in sorted(current.iterdir())
                if entry.name != part and not entry.is_symlink()
            ]
        current = current / part
    return tuple(denied)


@dataclass(frozen=True)
class AgentPolicy:
    """What an agent may do: edit files in ``worktree`` and run the listed commands.

    Build it with ``for_worktree``, which validates the commands.
    """

    worktree: Path
    """Absolute path of the folder the agent works in."""
    allowed_commands: tuple[str, ...]
    """The project's stack commands (``just test``), validated."""
    read_only_git: tuple[str, ...]
    denied_read_paths: tuple[str, ...]
    """Paths the sandbox denies reads of (``~/.ssh``, …, the SpoolHQ home)."""
    network_domains: tuple[str, ...] = ()
    """Domains the agent's commands may reach; none in v1."""
    read_only: bool = False
    """Only the read tools (Read, Glob, Grep): no Bash, Edit or Write. For the reviewer."""
    role: str = "implementer"
    """The role the policy is for, named when a backend refuses it."""

    @classmethod
    def for_worktree(cls, worktree: Path, commands: Mapping[str, str], home: Path) -> "AgentPolicy":
        """The policy for an agent in ``worktree`` that may run ``commands``.

        ``commands`` is ``project.yaml``'s ``commands`` (``{"test": "just test"}``);
        ``home`` is the SpoolHQ home folder, whose token the agent must never read.
        Raises PolicyError naming the field of the first bad command.
        """
        if not worktree.is_absolute():
            raise PolicyError(f"worktree must be an absolute path, got {str(worktree)!r}")
        if home.resolve() == worktree.resolve() or worktree.resolve() in home.resolve().parents:
            raise PolicyError(f"worktree {worktree} must not contain the SpoolHQ home {home}")
        allowed: list[str] = []
        for name, command in commands.items():
            check_command(f"commands.{name}", command)
            if command not in allowed:
                allowed.append(command)
        return cls(
            worktree=worktree,
            allowed_commands=tuple(allowed),
            read_only_git=READ_ONLY_GIT,
            denied_read_paths=(*CREDENTIAL_PATHS, *home_denials(home, worktree)),
        )

    @classmethod
    def read_only_for(cls, worktree: Path, home: Path, role: str = "reviewer") -> "AgentPolicy":
        """The policy for an agent (the reviewer or the planner) that may only read files
        in ``worktree``.

        It runs no commands, so it has no Bash rules; the sandbox settings and the
        deny list are the same as for a writing agent.
        """
        policy = cls.for_worktree(worktree, {}, home)
        return dataclasses.replace(policy, read_only_git=(), read_only=True, role=role)

    @property
    def commands(self) -> tuple[str, ...]:
        """Every command the agent may run: stack commands, then read-only git."""
        return (*self.allowed_commands, *self.read_only_git)

    def bash_rules(self) -> tuple[str, ...]:
        """Two permission rules per command: exact (``Bash(just test)``) and prefix."""
        return tuple(rule for cmd in self.commands for rule in (f"Bash({cmd})", f"Bash({cmd} *)"))


@dataclass(frozen=True)
class Budget:
    max_turns: int
    max_usd: Decimal | None
    """Estimated spend cap; only API-billed runs can enforce it."""
    max_tokens: int | None
    """Cap on weighted tokens (cache reads count a tenth), enforced by the runner."""
    timeout_s: float = 1800


# --- Events -------------------------------------------------------------------------


@dataclass(frozen=True)
class Started:
    model: str
    tools: tuple[str, ...]
    backend_version: str
    kind: str = field(default="started", init=False)


@dataclass(frozen=True)
class Message:
    text: str
    kind: str = field(default="message", init=False)


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    input_summary: str
    """The tool input as JSON, cut to 2,000 characters."""
    kind: str = field(default="tool_call", init=False)


@dataclass(frozen=True)
class FileEdit:
    path: str
    """Relative to the worktree, with forward slashes."""
    kind: str = field(default="file_edit", init=False)


@dataclass(frozen=True)
class Usage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int
    kind: str = field(default="usage", init=False)


@dataclass(frozen=True)
class PermissionDenied:
    tool: str
    input_summary: str
    reason: str
    kind: str = field(default="permission_denied", init=False)


@dataclass(frozen=True)
class RateLimit:
    status: str
    """``allowed``, ``allowed_warning``, ``rejected``, or ``retrying`` for an API retry."""
    reset_at: datetime | None
    kind: str = field(default="rate_limit", init=False)


AgentEvent = Started | Message | ToolCall | FileEdit | Usage | PermissionDenied | RateLimit


class Outcome(StrEnum):
    COMPLETED = "completed"
    MAX_TURNS = "max_turns"
    BUDGET_EXHAUSTED = "budget_exhausted"
    USAGE_LIMITED = "usage_limited"
    """A subscription usage limit; the run should pause until ``reset_at``."""
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass(frozen=True)
class RunResult:
    outcome: Outcome
    summary: str
    """The agent's final text, cut to 4,000 characters."""
    files_changed: tuple[str, ...]
    """Sorted, without duplicates, relative to the worktree (from file tools only)."""
    input_tokens: int
    """Every input token: uncached, cache writes and cache reads."""
    output_tokens: int
    cost_micro_usd: int | None
    """API-billed runs only; ``None`` for subscription runs."""
    reset_at: datetime | None
    denials: tuple[PermissionDenied, ...]
    num_turns: int
    backend: str
    backend_version: str
    model: str
    error: str | None
    debug: Mapping[str, int] = field(default_factory=dict)
    """Counters for troubleshooting, such as ``unknown_events``."""
    cache_read_tokens: int = 0
    """The part of ``input_tokens`` read from the prompt cache."""

    @property
    def weighted_tokens(self) -> int:
        return weighted_tokens(self.input_tokens, self.output_tokens, self.cache_read_tokens)


@dataclass(frozen=True)
class BackendInfo:
    name: str
    installed: bool
    version: str | None
    logged_in: bool
    auth_method: str | None
    billing: Billing
    policy_enforceable: bool
    reason: str | None
    """Why the backend can't run now, if it can't."""
    policy_parts: Mapping[str, Mapping[str, bool]] = field(default_factory=dict)
    """Role -> policy part -> whether the backend enforces it here; empty when it
    enforces the whole policy or nothing (Claude Code)."""

    @property
    def usable(self) -> bool:
        return self.installed and self.logged_in and self.policy_enforceable
