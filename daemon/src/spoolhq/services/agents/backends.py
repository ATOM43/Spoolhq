"""The agent backends SpoolHQ knows about, for detection and listing."""

from spoolhq.services.agents.claude_cli import ClaudeCliRunner
from spoolhq.services.agents.runner import AgentRunner


def available_runners() -> list[AgentRunner]:
    """One runner per supported backend; only ``claude-code-cli`` for now."""
    return [ClaudeCliRunner()]
