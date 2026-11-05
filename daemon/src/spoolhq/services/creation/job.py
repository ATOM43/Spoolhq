"""One project creation, step by step, with rollback of only what it created.

Steps: create the workspace, prepare the repo (Copier, a check only, or ``git init``),
check the stack commands through the gates, make the initial commit. Every path the
job creates is recorded as it is created; on a failure or cancel exactly those are
deleted, newest first, without following symlinks. An empty folder that existed keeps
existing, emptied of what the job wrote; an existing repo is never written to.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import spoolhq
from spoolhq.services.creation.request import Checked
from spoolhq.services.gates import GateName, GateStatus, try_command
from spoolhq.services.git import (
    DirtyRepoError,
    GitError,
    commit_staged,
    ensure_clean,
    remove_path,
    run_git,
)
from spoolhq.services.projects import ProjectError, init_project
from spoolhq.services.templates import (
    TemplateError,
    check_safe,
    init_repo,
    load_contract,
    open_template,
    render,
)

StepState = Literal["pending", "running", "passed", "failed", "skipped"]
JobState = Literal["running", "succeeded", "failed", "cancelled"]
STEPS = (
    ("workspace", "Create workspace"),
    ("repo", "Prepare repo"),
    ("commands", "Check commands"),
    ("commit", "Initial commit"),
)
TIMEOUTS_S: dict[GateName, float] = {"install": 600.0, "lint": 300.0, "test": 300.0}
EMPTY_COMMIT_MESSAGE = "Initial commit (SpoolHQ)"
GATE_MESSAGES = {
    GateStatus.FAILED: "The {gate} command failed",
    GateStatus.TIMED_OUT: "The {gate} command timed out",
    GateStatus.ERROR: "The {gate} command couldn't start",
}

logger = logging.getLogger(__name__)


@dataclass
class Step:
    name: str
    title: str
    state: StepState = "pending"
    duration_s: float | None = None
    passed: list[str] = field(default_factory=list)
    """For ``commands``: the gates that passed so far, in order."""
    message: str | None = None
    """For a failure: a fixed message, never request text."""
    output: str | None = None
    """For a failure: the trimmed output or error."""
    field: str | None = None
    """For a failure: the request field that caused it, like ``commands.test``."""


@dataclass
class Rollback:
    removed: list[str] = field(default_factory=list)
    left: list[str] = field(default_factory=list)
    """Paths that couldn't be deleted and are still there."""


@dataclass
class Job:
    id: str
    project: str
    source: str
    state: JobState = "running"
    steps: list[Step] = field(default_factory=lambda: [Step(*step) for step in STEPS])
    rollback: Rollback | None = None
    ended_at: float | None = None
    """``time.monotonic()`` when it ended."""


class _Failed(Exception):
    def __init__(self, message: str, field: str | None, output: str | None = None) -> None:
        super().__init__(message)
        self.message, self.field, self.output = message, field, output


class _Cancelled(Exception):
    pass


Created = list[tuple[Path, Literal["path", "contents", "empty_dir"]]]
"""``path``: delete it; ``contents``: a folder that existed empty, delete what's in it;
``empty_dir``: delete the folder only if it is still empty."""


def roll_back(created: Created) -> Rollback:
    """Delete what the job recorded, newest first, never following a symlink."""
    outcome = Rollback()
    for path, kind in reversed(created):
        targets = [path]
        if kind == "contents":
            targets = list(path.iterdir()) if path.is_dir() and not path.is_symlink() else []
        for target in targets:
            try:
                if kind != "empty_dir":
                    remove_path(target)
                elif target.is_dir() and not any(target.iterdir()):
                    target.rmdir()
                else:
                    continue  # another project is in it now
            except OSError:
                logger.warning("rollback left a path", extra={"path": str(target)})
                outcome.left.append(str(target))
                continue
            outcome.removed.append(str(target))
    return outcome


class Runner:
    """Runs one job's steps; ``lock`` guards ``job`` against readers on other threads."""

    def __init__(
        self,
        job: Job,
        checked: Checked,
        *,
        projects_dir: Path,
        cancel: threading.Event,
        lock: threading.Lock,
    ) -> None:
        self.job, self.checked, self.projects_dir = job, checked, projects_dir
        self.cancel, self.lock = cancel, lock
        self.created: Created = []
        self.template_ref = checked.template_ref
        self.template_name = checked.request.template
        """For a git template, the commit step 1 read, so step 2 renders the same one."""

    def _set(self, step: Step, **changes: object) -> None:
        with self.lock:
            for key, value in changes.items():
                setattr(step, key, value)

    def run(self) -> None:
        """All steps; on a failure, cancel or interrupt, roll back and end the job."""
        current: Step | None = None
        started = 0.0
        try:
            for step in self.job.steps:
                if self.cancel.is_set():
                    raise _Cancelled
                current, started = step, time.monotonic()
                self._set(step, state="running")
                skipped = getattr(self, f"_{step.name}")()
                state = "skipped" if skipped else "passed"
                self._set(step, state=state, duration_s=round(time.monotonic() - started, 3))
                current = None
            self._end("succeeded")
        except _Cancelled:
            self._fail(current, started, "Cancelled", None, None)
            self._end("cancelled", roll_back(self.created))
        except _Failed as exc:
            self._fail(current, started, exc.message, exc.field, exc.output)
            self._end("cancelled" if self.cancel.is_set() else "failed", roll_back(self.created))
        except BaseException as exc:
            logger.exception("project creation failed", extra={"project": self.job.project})
            self._fail(current, started, "Unexpected error", None, str(exc))
            self._end("failed", roll_back(self.created))
            if not isinstance(exc, Exception):
                raise

    def _fail(
        self, step: Step | None, started: float, message: str, field: str | None, out: str | None
    ) -> None:
        if step is not None:
            duration = round(time.monotonic() - started, 3)
            self._set(
                step, state="failed", duration_s=duration, message=message, field=field, output=out
            )

    def _end(self, state: JobState, rollback: Rollback | None = None) -> None:
        with self.lock:
            self.job.state, self.job.rollback = state, rollback
            self.job.ended_at = time.monotonic()

    # --- steps: each returns True when it was skipped ---------------------------------

    def _workspace(self) -> bool:
        request, checked = self.checked.request, self.checked
        if not self.projects_dir.exists():
            self.projects_dir.mkdir(parents=True)
            self.created.append((self.projects_dir, "empty_dir"))
        template, description = None, None
        if request.template is not None:
            try:
                with open_template(request.template, self.template_ref) as found:
                    contract = load_contract(found.root, found.label)
            except TemplateError as exc:
                raise _Failed("Couldn't read the template", "template", str(exc)) from exc
            if found.kind == "git":
                self.template_ref = found.ref
            template = {"name": contract.name, "source": found.source, "ref": found.ref}
            self.template_name = contract.name
            description = contract.description
        try:
            result = init_project(
                request.name,
                checked.repo,
                projects_dir=self.projects_dir,
                branch=checked.branch,
                remote=request.git_remote,
                commands=checked.commands,
                template=template,
                template_description=description,
                extra=checked.settings(),
                check_repo=request.source == "existing",
            )
        except ProjectError as exc:
            raise _Failed("Couldn't create the project workspace", "name", str(exc)) from exc
        self.created.append((result.path, "path"))
        return False

    def _repo(self) -> bool:
        request, repo = self.checked.request, self.checked.repo
        if request.source == "existing":
            try:
                ensure_clean(repo)
            except DirtyRepoError as exc:
                raise _Failed(
                    "The repository has uncommitted changes", "repo_path", str(exc)
                ) from exc
            return False
        if self.checked.repo_existed:
            self.created.append((repo, "contents"))
        else:
            repo.mkdir()
            self.created.append((repo, "path"))
        if request.source == "empty":
            try:
                run_git(
                    ["init", "--quiet", f"--initial-branch={self.checked.branch}"], repo
                ).check()
            except GitError as exc:
                raise _Failed("git init failed", "repo_path", str(exc)) from exc
            return False
        assert request.template is not None  # noqa: S101 - checked by check_request
        try:
            with open_template(request.template, self.template_ref) as template:
                check_safe(template.root, template.label)
                render(template, repo, request.name)
        except TemplateError as exc:
            raise _Failed("Couldn't generate the project", "template", str(exc)) from exc
        return False

    def _commands(self) -> bool:
        if not self.checked.commands:
            return True
        step = self.job.steps[2]
        for gate, command in self.checked.commands.items():
            name: GateName = gate  # type: ignore[assignment]  # keys are gate names
            result = try_command(name, command, self.checked.repo, TIMEOUTS_S[name], self.cancel)
            if self.cancel.is_set():
                raise _Cancelled
            if result.status is not GateStatus.PASSED:
                message = GATE_MESSAGES[result.status].format(gate=gate)
                raise _Failed(message, f"commands.{gate}", result.excerpt)
            self._set(step, passed=[*step.passed, gate])
        return False

    def _commit(self) -> bool:
        request, repo = self.checked.request, self.checked.repo
        if request.source == "existing":
            return True
        try:
            if request.source == "empty":
                commit_staged(repo, EMPTY_COMMIT_MESSAGE, allow_empty=True)
            else:
                message = f"chore: generate from {self.template_name} {spoolhq.__version__}"
                init_repo(repo, self.checked.branch, message)
        except GitError as exc:
            raise _Failed("Couldn't make the initial commit", "repo_path", str(exc)) from exc
        return False
