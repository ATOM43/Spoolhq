"""Runs: the record of every run and attempt of a workspace, and its event stream.

``state.db`` in ``<workspace>/.spoolhq/`` holds runs, attempts and append-only events
(``RunLog``); each attempt has a folder of files under ``<workspace>/runs/``; an
in-process ``EventBus`` fans committed events out to subscribers; and
``recover_interrupted`` closes runs a stopped daemon left active. The run loop that
drives these is ``services/runloop``. See ``docs/runs.md``.
"""

from spoolhq.services.runs.bus import EventBus, Subscription
from spoolhq.services.runs.db import (
    SCHEMA_VERSION,
    RunLogError,
    format_ts,
    state_db_path,
    utc_now,
)
from spoolhq.services.runs.files import (
    ARTIFACT_NAMES,
    ArtifactName,
    append_transcript,
    attempt_dir,
    attempt_files,
    write_artifact,
)
from spoolhq.services.runs.journal import (
    Integration,
    IntegrationState,
    get_integration,
    last_integration,
    open_integrations,
    set_integration_state,
    start_integration,
)
from spoolhq.services.runs.log import RunLog
from spoolhq.services.runs.model import (
    PLAN_RUN_ID,
    TERMINAL_RUN_STATUSES,
    Attempt,
    AttemptKind,
    AttemptStatus,
    Event,
    EventKind,
    Run,
    RunKind,
    RunStatus,
    Usage,
)
from spoolhq.services.runs.recovery import INTERRUPTED_REASON, recover_interrupted
from spoolhq.services.runs.registry import RunRegistry, WorkspaceRuns
from spoolhq.services.runs.rows import MAX_PAYLOAD_BYTES

__all__ = [
    "ARTIFACT_NAMES",
    "INTERRUPTED_REASON",
    "MAX_PAYLOAD_BYTES",
    "SCHEMA_VERSION",
    "TERMINAL_RUN_STATUSES",
    "ArtifactName",
    "Attempt",
    "AttemptKind",
    "AttemptStatus",
    "Event",
    "Integration",
    "IntegrationState",
    "EventBus",
    "EventKind",
    "PLAN_RUN_ID",
    "Run",
    "RunKind",
    "RunLog",
    "RunLogError",
    "RunRegistry",
    "RunStatus",
    "Subscription",
    "Usage",
    "WorkspaceRuns",
    "append_transcript",
    "attempt_dir",
    "attempt_files",
    "format_ts",
    "get_integration",
    "last_integration",
    "open_integrations",
    "recover_interrupted",
    "set_integration_state",
    "start_integration",
    "state_db_path",
    "utc_now",
    "write_artifact",
]
