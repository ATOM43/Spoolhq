"""Project creation: a job that makes a project from a template, an existing repo or an
empty repo, step by step, and rolls back only what it created. ``check_request`` refuses
an unsafe path or template before any job starts; ``inspect_repo`` reads what an
existing repo already has. This package may import ``services.projects``,
``services.templates``, ``services.gates``, ``services.git`` and (for its settings list)
``services.agents``.
See ``docs/api.md``.
"""

from spoolhq.services.creation.inspect import DetectedCommands, RepoInspection, inspect_repo
from spoolhq.services.creation.job import (
    EMPTY_COMMIT_MESSAGE,
    STEPS,
    Job,
    Rollback,
    Runner,
    Step,
    roll_back,
)
from spoolhq.services.creation.jobs import CreationJobs, UnknownJobError
from spoolhq.services.creation.request import (
    MERGE_PRESETS,
    NAME_RULE,
    Checked,
    CreateProject,
    CreationError,
    Local,
    StackCommands,
    check_request,
)

__all__ = [
    "EMPTY_COMMIT_MESSAGE",
    "MERGE_PRESETS",
    "NAME_RULE",
    "STEPS",
    "Checked",
    "CreateProject",
    "CreationError",
    "CreationJobs",
    "DetectedCommands",
    "RepoInspection",
    "Job",
    "Local",
    "Rollback",
    "Runner",
    "StackCommands",
    "Step",
    "UnknownJobError",
    "check_request",
    "inspect_repo",
    "roll_back",
]
