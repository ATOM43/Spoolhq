"""Projects: creating, listing and loading SpoolHQ projects."""

from spoolhq.services.projects.errors import ProjectError, ProjectValidationError
from spoolhq.services.projects.model import (
    AGENT_BACKENDS,
    Agents,
    Budget,
    Commands,
    ContextSettings,
    GitSettings,
    Limits,
    MergePolicy,
    Project,
    TemplateInfo,
    Tracker,
)
from spoolhq.services.projects.workspace import (
    InitResult,
    init_project,
    list_workspaces,
    load_project,
    project_dir,
    save_project,
    template_description,
)

__all__ = [
    "AGENT_BACKENDS",
    "Agents",
    "Budget",
    "Commands",
    "ContextSettings",
    "GitSettings",
    "InitResult",
    "Limits",
    "MergePolicy",
    "Project",
    "ProjectError",
    "ProjectValidationError",
    "TemplateInfo",
    "Tracker",
    "init_project",
    "list_workspaces",
    "load_project",
    "project_dir",
    "save_project",
    "template_description",
]
