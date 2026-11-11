"""The event WebSocket's messages. ``data`` is the event's payload; its shape per
``type`` is one of the ``*Data`` models (added to the OpenAPI components for the
TypeScript client). Payload text is untrusted (ticket and agent text)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from spoolhq.services.runs import Event


class EventEnvelope(BaseModel):
    seq: int
    """The event's id in the run log: it only grows, so a client reconnects with
    ``since=<last seq>``."""
    run_id: int
    attempt: int | None
    """The attempt's number (as in the artifact URL), if the event belongs to one."""
    ticket: str | None
    """The run's ticket id (``plan`` for a plan run)."""
    type: str
    """``run.started``, ``run.status``, ``run.phase``, ``attempt.started``, …"""
    ts: str
    data: dict[str, Any]

    @classmethod
    def of(cls, event: Event, ticket: str | None, attempt: int | None) -> "EventEnvelope":
        return cls(
            seq=event.id,
            run_id=event.run_id,
            attempt=attempt,
            ticket=ticket,
            type=event.kind.value,
            ts=event.ts,
            data=event.payload,
        )


class AuthMessage(BaseModel):
    """The client's first message, within 5 s."""

    type: Literal["auth"]
    token: str


class _Data(BaseModel):
    model_config = ConfigDict(extra="allow")


class RunStartedData(_Data):
    ticket_id: str
    kind: str | None = None


class RunStatusData(_Data):
    from_: str = Field(alias="from")
    to: str
    reason: str | None = None
    reset_at: str | None = None


class RunInterruptedData(_Data):
    reason: str
    attempt_ids: list[int]


class RunPhaseData(_Data):
    phase: str
    text: str
    """The line ``spool run`` prints."""


class AttemptStartedData(_Data):
    number: int
    kind: str
    dir: str
    backend: str | None
    model: str | None


class AttemptFinishedData(_Data):
    number: int
    status: str


class LogData(_Data):
    message: str | None = None
    user_note: str | None = None
    pr_review: str | None = None


class IntegrateData(_Data):
    commit: str
    tag: str
    pr: int | None = None


class PolicyDecisionData(_Data):
    mode: str
    rules: list[dict[str, str]]


class EventList(BaseModel):
    """``GET …/runs/{run_id}/events``: stored events, oldest first."""

    items: list[EventEnvelope]
    next_after: int | None
    """Pass it as ``after`` for the next page; null on the last page."""
    total: int
    """Every event of the run (or of the attempt, with ``attempt=``), whatever ``after``
    is: the denominator of a loading bar."""


class GateDoneData(_Data):
    name: str
    command: str
    status: str
    duration_ms: int


class StepData(_Data):
    step: Literal["worktree", "implement", "gates", "review", "policy", "integrate"]
    state: Literal["running", "passed", "failed", "skipped"]
    attempt: int
    gate: str | None = None
    """The gates step only: the gate starting now (``install``, ``lint``, ``test``)."""
    command: str | None = None
    """With ``gate``: its command line."""
    done: list[GateDoneData] | None = None
    """With ``gate``: the gates finished so far, without their output."""


class AgentMessageData(_Data):
    text: str


class AgentToolCallData(_Data):
    id: str
    name: str
    input_summary: str


class AgentToolResultData(_Data):
    id: str
    text: str
    """The first 200 lines."""
    lines: int
    """How many lines the result had."""
    is_error: bool


class AgentFileEditData(_Data):
    path: str
    added: int | None
    removed: int | None


class AgentUsageData(_Data):
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_creation_tokens: int


class AgentDeniedData(_Data):
    tool: str
    input_summary: str
    reason: str


class AgentRateLimitData(_Data):
    status: str
    reset_at: str | None


class AgentWarningData(_Data):
    text: str
    line: str


EVENT_DATA_MODELS: tuple[type[BaseModel], ...] = (
    EventEnvelope,
    AuthMessage,
    RunStartedData,
    RunStatusData,
    RunInterruptedData,
    RunPhaseData,
    AttemptStartedData,
    AttemptFinishedData,
    LogData,
    IntegrateData,
    PolicyDecisionData,
    StepData,
    AgentMessageData,
    AgentToolCallData,
    AgentToolResultData,
    AgentFileEditData,
    AgentUsageData,
    AgentDeniedData,
    AgentRateLimitData,
    AgentWarningData,
)
