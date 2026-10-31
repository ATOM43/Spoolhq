"""Agents: the planner, implementer and reviewer behind the AgentRunner interface.

A runner runs one coding-agent session in a worktree under an ``AgentPolicy`` and
returns a ``RunResult``. ``ClaudeCliRunner`` drives the user's own ``claude`` CLI;
the policy is enforced by Claude Code (restricted mode, an allowlist, the OS sandbox
and a scrubbed environment) and verified from its stream. ``CodexCliRunner`` drives
``codex exec`` under a per-run permission profile and refuses what Codex can't enforce.
``AgentSdkRunner`` runs the Claude Agent SDK with an API key, the same policy layers
and a ``PreToolUse`` hook. ``FakeRunner`` replays recorded transcripts for tests. This
package imports no other service. See
``docs/agents.md``.
"""

from spoolhq.core.agent_policy import READ_ONLY_GIT
from spoolhq.services.agents.agent_sdk import AgentSdkRunner
from spoolhq.services.agents.backends import (
    READ_ONLY_SHELL,
    available_runners,
    backend_names,
    make_runner,
)
from spoolhq.services.agents.claude_cli import MIN_VERSION, ClaudeCliRunner
from spoolhq.services.agents.claude_stream import ClaudeStreamParser, PolicyViolation
from spoolhq.services.agents.codex_cli import CodexCliRunner
from spoolhq.services.agents.codex_config import temp_worktree_refusal
from spoolhq.services.agents.codex_stream import CodexStreamParser
from spoolhq.services.agents.fake import FakeRunner
from spoolhq.services.agents.model import (
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
    "READ_ONLY_SHELL",
    "AgentEvent",
    "AgentPolicy",
    "AgentSdkRunner",
    "AgentRunner",
    "BackendInfo",
    "BackendUnavailableError",
    "Budget",
    "ClaudeCliRunner",
    "ClaudeStreamParser",
    "CodexCliRunner",
    "CodexStreamParser",
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
    "temp_worktree_refusal",
    "available_runners",
    "backend_names",
    "make_runner",
]
