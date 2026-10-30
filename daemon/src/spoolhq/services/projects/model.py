"""The ``project.yaml`` model.

Every model forbids unknown keys, so a typo is an error rather than a silently ignored
setting. Validation also checks the repository on disk (read-only git calls).
"""

import re
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from spoolhq.services.agents import AgentRunner, backend_names, make_runner
from spoolhq.services.gates import DEFAULT_TIMEOUTS, check_gate_command
from spoolhq.services.git import (
    GitError,
    github_repo,
    has_local_branch,
    is_branch_name,
    is_work_tree,
)

Role = Literal["planner", "implementer", "reviewer"]
LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]{0,62}")
SLUG_RULE = "must be 1-63 lowercase letters, digits or hyphens, starting with a letter or digit"

LOCKFILES = (
    "uv.lock",
    "poetry.lock",
    "pnpm-lock.yaml",
    "package-lock.json",
    "yarn.lock",
    "Cargo.lock",
)
"""File names that don't count toward the merge policy's diff size (they are protected)."""
DEFAULT_PROTECTED_PATHS = (
    # CI and tooling
    ".github/**",
    "justfile",
    "Makefile",
    "**/Dockerfile",
    "docker-compose*.yml",
    # migrations
    "**/migrations/**",
    "**/alembic/**",
    # auth and security
    "**/auth/**",
    "**/*auth*.py",
    "**/security/**",
    # dependencies
    "**/pyproject.toml",
    "**/package.json",
    "**/Cargo.toml",
    *(f"**/{name}" for name in LOCKFILES),
    # agent instructions
    "CLAUDE.md",
    "**/CLAUDE.md",
    ".claude/**",
    "prompts/**",
)

# Set as validation context by load_project, so `name` must match the folder name.
FOLDER_NAME_CONTEXT = "folder_name"


def check_slug(value: str) -> str:
    if not SLUG_RE.fullmatch(value):
        raise ValueError(SLUG_RULE)
    return value


def check_github_url(value: str) -> str:
    try:
        github_repo(value)
    except ValueError:
        raise ValueError("not a GitHub URL") from None
    return value


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


def _check_base_url(value: str) -> str:
    """http(s) only, plain http only to this machine, and no credentials in the URL."""
    try:
        parts = urlsplit(value)
        parts.port  # noqa: B018 - raises ValueError for a bad port
    except ValueError as exc:
        raise ValueError(f"{value!r} is not a valid URL") from exc
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"{value!r} must be an http or https URL")
    if parts.username is not None or parts.password is not None:
        raise ValueError("must not contain a username or password")
    if parts.scheme == "http" and parts.hostname not in LOOPBACK_HOSTS:
        raise ValueError(f"{value!r}: plain http is allowed only for localhost; use https")
    return value


def _check_backend(value: str) -> str:
    names = backend_names()
    if value not in names:
        raise ValueError(f"unknown backend {value!r}; expected one of: {', '.join(names)}")
    return value


BackendName = Annotated[str, AfterValidator(_check_backend)]


class BackendSettings(_Strict):
    """A custom endpoint and model for one backend, e.g. a local Ollama server."""

    base_url: Annotated[str, AfterValidator(_check_base_url)] | None = None
    model: NonEmptyStr | None = None


class Agents(_Strict):
    default: BackendName = "claude-code-cli"
    planner: BackendName | None = None
    implementer: BackendName | None = None
    reviewer: BackendName | None = None
    backends: dict[BackendName, BackendSettings] = Field(default_factory=dict)
    budget_per_ticket: Budget | None = None

    def backend_for(self, role: Role) -> str:
        """The role's backend: its override, or ``default``."""
        override: str | None = getattr(self, role)
        return override or self.default

    def runner_for(self, role: Role) -> AgentRunner:
        """The role's runner, with its backend's ``base_url`` and ``model``."""
        name = self.backend_for(role)
        backend = self.backends.get(name, BackendSettings())
        return make_runner(name, base_url=backend.base_url, model=backend.model)


class Limits(_Strict):
    gate_retries: int = Field(default=3, ge=0, le=10)
    review_retries: int = Field(default=2, ge=0, le=10)


def _check_path_pattern(value: str) -> str:
    if value.startswith(("/", "\\")) or re.match(r"[A-Za-z]:", value):
        raise ValueError(f"must be a repo-relative pattern, got {value!r}")
    if ".." in value.split("/"):
        raise ValueError(f"must not contain '..', got {value!r}")
    return value


PathPattern = Annotated[NonEmptyStr, AfterValidator(_check_path_pattern)]


class MergePolicy(_Strict):
    """When an approved ticket needs a person (docs/merge-policy.md)."""

    max_diff_lines: int = Field(default=400, ge=10, le=100_000)
    protected_paths: list[PathPattern] = Field(
        default_factory=lambda: list(DEFAULT_PROTECTED_PATHS)
    )
    """Replaces the default list."""
    protected_paths_extra: list[PathPattern] = Field(default_factory=list)
    """Added to ``protected_paths``."""

    def protected(self) -> list[str]:
        return [*self.protected_paths, *self.protected_paths_extra]


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


class TemplateInfo(_Strict):
    """The stack template the repository was generated from (``spool init --template``)."""

    name: NonEmptyStr
    source: NonEmptyStr
    """The built-in name, the local folder or the git URL given to ``--template``."""
    ref: NonEmptyStr | None = None
    """The resolved commit (git templates) or SpoolHQ's version (built-ins)."""


class Project(_Strict):
    name: str
    repo: str
    default_branch: NonEmptyStr = Field(default="main", validate_default=True)
    template: TemplateInfo | None = None
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
