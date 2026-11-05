"""Project creation: a job that makes a project from a template, an existing repo or an
empty repo, step by step, and rolls back only what it created. ``check_request`` refuses
an unsafe path or template before any job starts. This package may import
``services.projects``, ``services.templates``, ``services.gates`` and ``services.git``.
See ``docs/api.md``.
"""

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
    "Job",
    "Rollback",
    "Runner",
    "StackCommands",
    "Step",
    "UnknownJobError",
    "check_request",
    "roll_back",
]
