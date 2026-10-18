"""Agents: the planner, implementer and reviewer behind the AgentRunner interface.

A runner runs one coding-agent session in a worktree under an ``AgentPolicy`` and
returns a ``RunResult``. ``ClaudeCliRunner`` drives the user's own ``claude`` CLI;
the policy is enforced by Claude Code (restricted mode, an allowlist, the OS sandbox
and a scrubbed environment) and verified from its stream. ``FakeRunner`` replays
recorded transcripts for tests. This package imports no other service. See
``docs/agents.md``.
"""

from spoolhq.services.agents.backends import available_runners
from spoolhq.services.agents.claude_cli import MIN_VERSION, ClaudeCliRunner
from spoolhq.services.agents.claude_stream import ClaudeStreamParser, PolicyViolation
from spoolhq.services.agents.fake import FakeRunner
from spoolhq.services.agents.model import (
    READ_ONLY_GIT,
    AgentEvent,
    AgentPolicy,
    BackendInfo,
    Budget,
    FileEdit,
    Message,
    Outcome,
    PermissionDenied,
    PolicyError,
    RateLimit,
    RunResult,
    Started,
    ToolCall,
    Usage,
)
from spoolhq.services.agents.runner import AgentRunner, BackendUnavailableError

__all__ = [
    "MIN_VERSION",
    "READ_ONLY_GIT",
    "AgentEvent",
    "AgentPolicy",
    "AgentRunner",
    "BackendInfo",
    "BackendUnavailableError",
    "Budget",
    "ClaudeCliRunner",
    "ClaudeStreamParser",
    "FakeRunner",
    "FileEdit",
    "Message",
    "Outcome",
    "PermissionDenied",
    "PolicyError",
    "PolicyViolation",
    "RateLimit",
    "RunResult",
    "Started",
    "ToolCall",
    "Usage",
    "available_runners",
]
