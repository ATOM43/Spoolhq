"""The agent backends SpoolHQ knows about: a registry from name to adapter factory.

``project.yaml``'s ``agents.*`` names a backend; ``make_runner`` builds its runner with
the optional custom endpoint (``base_url``) and ``model`` from ``agents.backends``.
"""

from collections.abc import Callable

from spoolhq.services.agents.claude_cli import ClaudeCliRunner
from spoolhq.services.agents.claude_stream import BACKEND_NAME
from spoolhq.services.agents.codex_cli import CodexCliRunner
from spoolhq.services.agents.codex_config import BACKEND_NAME as CODEX_NAME
from spoolhq.services.agents.runner import AgentRunner

BackendFactory = Callable[[str | None, str | None], AgentRunner]
"""``factory(base_url, model)`` builds a runner for that endpoint and model."""

BACKENDS: dict[str, BackendFactory] = {
    # Tests add fakes here (the ``fake_backend`` fixture).
    BACKEND_NAME: lambda base_url, model: ClaudeCliRunner(base_url=base_url, model=model),
    CODEX_NAME: lambda base_url, model: CodexCliRunner(base_url=base_url, model=model),
}


def backend_names() -> tuple[str, ...]:
    """The registered backend names, in registration order."""
    return tuple(BACKENDS)


def make_runner(name: str, *, base_url: str | None = None, model: str | None = None) -> AgentRunner:
    """The runner for backend ``name``; ValueError for an unknown name."""
    factory = BACKENDS.get(name)
    if factory is None:
        raise ValueError(f"unknown backend {name!r}; expected one of: {', '.join(BACKENDS)}")
    return factory(base_url, model)


def available_runners() -> list[AgentRunner]:
    """One runner per supported backend, for detection."""
    return [ClaudeCliRunner(), CodexCliRunner()]
