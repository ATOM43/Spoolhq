"""The ``AgentRunner`` interface every coding-agent backend implements."""

import threading
from collections.abc import Callable
from typing import Any, Protocol

from spoolhq.services.agents.model import (
    AgentEvent,
    AgentPolicy,
    BackendInfo,
    Budget,
    PolicyError,
    RunResult,
)

EventCallback = Callable[[AgentEvent], None]
RawCallback = Callable[[dict[str, Any]], None]

__all__ = [
    "AgentRunner",
    "BackendUnavailableError",
    "EventCallback",
    "PolicyError",
    "RawCallback",
]


class BackendUnavailableError(RuntimeError):
    """The backend isn't installed, isn't logged in, or can't enforce the policy."""


class AgentRunner(Protocol):
    """Runs one coding-agent session in a worktree under an ``AgentPolicy``.

    ``on_event`` gets the normalised events in order and ``on_raw`` every raw
    stream message (for ``transcript.jsonl``). Callbacks run on the calling thread or
    one reader thread, never concurrently. ``run`` calls ``detect`` first and raises
    BackendUnavailableError with its reason when the backend can't run; everything
    that happens once the agent started is reported in the ``RunResult``'s outcome.
    """

    name: str

    def detect(self) -> BackendInfo: ...

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
    ) -> RunResult: ...
