"""Request and response models of ``POST /api/repos/inspect``."""

from pydantic import BaseModel, ConfigDict, Field


class InspectRepo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=4096)
    """Absolute path of the repo, as for ``repo_path`` in ``POST /api/projects``."""


class DetectedCommandsView(BaseModel):
    install: str | None
    lint: str | None
    test: str | None
    source: str | None
    """The file the commands came from (``justfile``, ``Makefile``, ``package.json``,
    ``pyproject.toml``); null when none was detected."""


class RepoInspectionView(BaseModel):
    branch: str
    clean: bool
    dirty: list[str]
    """``git status`` entries when the repo isn't clean (``" M src/a.py"``)."""
    origin: str | None
    """``origin``'s URL when it points at GitHub, else null."""
    commands: DetectedCommandsView
    agent_settings: list[str]
    """The repo's own agent settings files, which runs ignore."""
    notes_missing: list[str]
    """Which of ``PROGRESS.md`` and ``DECISIONS.md`` don't exist."""
