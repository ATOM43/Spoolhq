"""The ``project.yaml`` model.

Every model forbids unknown keys, so a typo is an error rather than a silently ignored
setting. Validation also checks the repository on disk (read-only git calls).
"""

import re
from pathlib import Path
from typing import Annotated, Literal, get_args

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from spoolhq.services.gates import DEFAULT_TIMEOUTS, check_gate_command
from spoolhq.services.git import GitError, has_local_branch, is_branch_name, is_work_tree

AgentBackend = Literal["claude-code-cli", "codex-cli", "gemini-cli", "claude-agent-sdk"]
AGENT_BACKENDS: tuple[str, ...] = get_args(AgentBackend)

SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
SLUG_RULE = "must be 1-63 lowercase letters, digits or hyphens, starting with a letter or digit"
# GitHub's rules: an owner is 1-39 letters, digits or hyphens, not starting with a
# hyphen; a repository is 1-100 letters, digits, '.', '_' or '-', not starting with
# '-' or '.'.
_GITHUB_OWNER = r"(?P<owner>[A-Za-z0-9][A-Za-z0-9-]{0,38})"
_GITHUB_REPO = r"(?P<repo>[A-Za-z0-9_][A-Za-z0-9._-]{0,99}?)"
GITHUB_HTTPS_RE = re.compile(rf"https://github\.com/{_GITHUB_OWNER}/{_GITHUB_REPO}(?:\.git)?")
GITHUB_SSH_RE = re.compile(rf"git@github\.com:{_GITHUB_OWNER}/{_GITHUB_REPO}\.git")

DEFAULT_PROTECTED_PATHS = ["**/migrations/**", ".github/**", "**/auth/**"]

# Set as validation context by load_project, so `name` must match the folder name.
FOLDER_NAME_CONTEXT = "folder_name"


def check_slug(value: str) -> str:
    if not SLUG_RE.fullmatch(value):
        raise ValueError(SLUG_RULE)
    return value


def check_github_url(value: str) -> str:
    if any(pattern.fullmatch(value) for pattern in (GITHUB_HTTPS_RE, GITHUB_SSH_RE)):
        return value
    raise ValueError("not a GitHub URL")


def _check_not_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    return value


NonEmptyStr = Annotated[str, AfterValidator(_check_not_blank)]
# Run by the gates without a shell, so shell syntax is refused (docs/gates.md).
GateCommand = Annotated[NonEmptyStr, AfterValidator(check_gate_command)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Commands(_Strict):
    install: GateCommand
    lint: GateCommand
    test: GateCommand

    def for_implementer(self) -> dict[str, str]:
        """The commands the implementer may run: all but ``install``, which only the gates
        run, outside the sandbox (DECISIONS 91)."""
        return {name: cmd for name, cmd in self.model_dump().items() if name != "install"}


class Budget(_Strict):
    usd: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    tokens: int | None = Field(default=None, gt=0)


class Agents(_Strict):
    default: AgentBackend = "claude-code-cli"
    planner: AgentBackend | None = None
    implementer: AgentBackend | None = None
    reviewer: AgentBackend | None = None
    budget_per_ticket: Budget | None = None

    @field_validator("default", "planner", "implementer", "reviewer", mode="before")
    @classmethod
    def _known_backend(cls, value: object) -> object:
        # Runs before the Literal check so the message lists the backends.
        if isinstance(value, str) and value not in AGENT_BACKENDS:
            expected = ", ".join(AGENT_BACKENDS)
            raise ValueError(f"unknown backend {value!r}; expected one of: {expected}")
        return value


class Limits(_Strict):
    gate_retries: int = Field(default=3, ge=0, le=10)
    review_retries: int = Field(default=2, ge=0, le=10)


class MergePolicy(_Strict):
    max_direct_diff_lines: int = Field(default=400, gt=0)
    protected_paths: list[NonEmptyStr] = Field(
        default_factory=lambda: list(DEFAULT_PROTECTED_PATHS)
    )
    always_pr: bool = False


class GitSettings(_Strict):
    remote: Annotated[str, AfterValidator(check_github_url)] | None = None


class ContextSettings(_Strict):
    """The implementer prompt's size budget and history depth (see docs/context.md)."""

    max_chars: int = Field(default=120_000, ge=20_000, le=2_000_000)
    progress_entries: int = Field(default=3, ge=1, le=1_000)
    """How many of the newest ``PROGRESS.md`` entries the prompt includes."""
    decisions_lines: int = Field(default=20, ge=1, le=10_000)
    """How many of the newest non-blank ``DECISIONS.md`` lines the prompt includes."""


class GateTimeouts(_Strict):
    """Seconds each gate may run before its process tree is stopped (docs/gates.md)."""

    install: int = Field(default=DEFAULT_TIMEOUTS["install"], ge=10, le=7_200)
    lint: int = Field(default=DEFAULT_TIMEOUTS["lint"], ge=10, le=7_200)
    test: int = Field(default=DEFAULT_TIMEOUTS["test"], ge=10, le=7_200)


class GatesSettings(_Strict):
    timeouts: GateTimeouts = Field(default_factory=GateTimeouts)


class RunSettings(_Strict):
    """``integration``: ``local`` merges approved tickets into the default branch;
    ``hold`` waits for ``spool run integrate`` (docs/integration.md)."""

    integration: Literal["local", "hold"] = "local"


class Tracker(_Strict):
    kind: Literal["clickup"] = "clickup"
    list_id: NonEmptyStr


class Project(_Strict):
    name: str
    repo: str
    default_branch: NonEmptyStr = Field(default="main", validate_default=True)
    template: NonEmptyStr | None = None
    commands: Commands
    agents: Agents = Field(default_factory=Agents)
    limits: Limits = Field(default_factory=Limits)
    merge_policy: MergePolicy = Field(default_factory=MergePolicy)
    git: GitSettings = Field(default_factory=GitSettings)
    tracker: Tracker | None = None
    context: ContextSettings = Field(default_factory=ContextSettings)
    gates: GatesSettings = Field(default_factory=GatesSettings)
    run: RunSettings = Field(default_factory=RunSettings)

    @property
    def repo_path(self) -> Path:
        """The repository folder, with ``~`` expanded."""
        return Path(self.repo).expanduser()

    @field_validator("name")
    @classmethod
    def _name_is_slug(cls, value: str, info: ValidationInfo) -> str:
        check_slug(value)
        folder = (info.context or {}).get(FOLDER_NAME_CONTEXT)
        if folder is not None and value != folder:
            raise ValueError(f"{value!r} does not match the project folder name {folder!r}")
        return value

    @field_validator("repo")
    @classmethod
    def _repo_is_work_tree(cls, value: str) -> str:
        path = Path(value).expanduser()
        if not path.is_absolute():
            raise ValueError(f"must be an absolute path (or start with ~), got {value!r}")
        if not path.exists():
            raise ValueError(f"path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"not a folder: {path}")
        try:
            work_tree = is_work_tree(path)
        except GitError as exc:
            raise ValueError(str(exc)) from exc
        if not work_tree:
            raise ValueError(f"not a git work tree: {path}")
        return value

    @field_validator("default_branch")
    @classmethod
    def _branch_exists(cls, value: str, info: ValidationInfo) -> str:
        repo = info.data.get("repo")
        if repo is None:
            # The repo itself is invalid and already reported.
            return value
        path = Path(repo).expanduser()
        try:
            if not is_branch_name(path, value):
                raise ValueError(f"{value!r} is not a valid branch name")
            exists = has_local_branch(path, value)
        except GitError as exc:
            raise ValueError(str(exc)) from exc
        if not exists:
            raise ValueError(f"branch {value!r} not found in {path}")
        return value
