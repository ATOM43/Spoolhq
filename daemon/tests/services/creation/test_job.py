"""The creation job end to end: each source, a failure after every step, cancel."""

import hashlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

import spoolhq
from spoolhq.services.creation import (
    EMPTY_COMMIT_MESSAGE,
    CreateProject,
    CreationJobs,
    Job,
    Runner,
    UnknownJobError,
    roll_back,
)
from spoolhq.services.creation import job as job_module
from spoolhq.services.projects import load_project
from spoolhq.services.projects.yaml_io import parse
from tests.conftest import fake_tool_cmd, run_git

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("git_identity")]

PASS = {gate: fake_tool_cmd("pass") for gate in ("install", "lint", "test")}
STEP_NAMES = ["workspace", "repo", "commands", "commit"]


def jobs_for(projects_dir: Path, home: Path) -> CreationJobs:
    return CreationJobs(projects_dir=projects_dir, worktrees_dir=home / "worktrees", home=home)


def create(projects_dir: Path, home: Path, **fields: Any) -> Job:
    jobs = jobs_for(projects_dir, home)
    started = jobs.start(CreateProject.model_validate({"name": "demo", **fields}))
    return jobs.wait(started.id, 60)


def snapshot(root: Path) -> dict[str, str]:
    """Every path under ``root`` with its content hash. Left out: git's index (a
    read-only ``git status`` may refresh it) and the SpoolHQ home, where the git runner
    keeps its own empty hooks folder."""
    found: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.name == "index" and ".git" in path.parts:
            continue
        if "spoolhq-home" in path.relative_to(root).parts:
            continue
        rel = path.relative_to(root).as_posix()
        found[rel] = (
            hashlib.sha256(path.read_bytes()).hexdigest()
            if path.is_file() and not path.is_symlink()
            else "folder"
        )
    return found


def git_state(repo: Path) -> tuple[str, str, str]:
    return (
        run_git(repo, "status", "--porcelain", "--untracked-files=all"),
        run_git(repo, "rev-parse", "HEAD"),
        run_git(repo, "branch", "--list"),
    )


def source_fields(source: str, tmp_path: Path, git_repo: Path) -> dict[str, Any]:
    if source == "existing":
        return {"source": "existing", "repo_path": str(git_repo), "commands": PASS}
    fields: dict[str, Any] = {"source": source, "repo_path": str(tmp_path / "new")}
    if source == "template":
        fields.update(template="fixture", commands=PASS)
    return fields


def states(job: Job) -> list[str]:
    return [step.state for step in job.steps]


@pytest.mark.usefixtures("builtin_fixture")
def test_from_a_template(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    repo = tmp_path / "new"
    job = create(
        projects_dir,
        home,
        source="template",
        repo_path=str(repo),
        template="fixture",
        commands=PASS,
    )
    assert (job.state, states(job), job.rollback) == ("succeeded", ["passed"] * 4, None)
    assert run_git(repo, "log", "--format=%s").splitlines() == [
        f"chore: generate from fixture {spoolhq.__version__}"
    ]
    assert run_git(repo, "status", "--porcelain") == ""
    assert (repo / "README.md").read_text(encoding="utf-8") == "# demo\n"
    project = load_project("demo", projects_dir=projects_dir)
    assert project.template is not None
    assert (project.template.name, project.template.ref) == ("fixture", spoolhq.__version__)
    assert project.commands.test == PASS["test"]
    workspace = projects_dir / "demo"
    assert (workspace / "TEMPLATE.md").read_text(
        encoding="utf-8"
    ) == "A fixture template for tests."
    for name in ("project.yaml", "CONTEXT.md"):
        assert (workspace / name).is_file()
    for name in ("tickets", "runs"):
        assert (workspace / name).is_dir()


def test_from_an_existing_repo(
    tmp_path: Path, projects_dir: Path, home: Path, git_repo: Path
) -> None:
    before, git_before = snapshot(git_repo), git_state(git_repo)
    job = create(
        projects_dir,
        home,
        source="existing",
        repo_path=str(git_repo),
        commands=PASS,
        merge_preset="always_direct",
        git_remote="https://github.com/o/r",
    )
    assert (job.state, states(job)) == ("succeeded", ["passed", "passed", "passed", "skipped"])
    assert (snapshot(git_repo), git_state(git_repo)) == (before, git_before)
    project = load_project("demo", projects_dir=projects_dir)
    assert project.repo_path == git_repo.resolve()
    assert project.git.remote == "https://github.com/o/r"
    assert (project.merge_policy.max_diff_lines, project.merge_policy.protected_paths) == (
        100_000,
        [],
    )


@pytest.mark.parametrize("existed", [False, True], ids=["new-folder", "empty-folder"])
def test_from_an_empty_repo_without_commands(
    tmp_path: Path, projects_dir: Path, home: Path, existed: bool
) -> None:
    repo = tmp_path / "new"
    if existed:
        repo.mkdir()
    job = create(projects_dir, home, source="empty", repo_path=str(repo), clickup_list_id="9")
    assert (job.state, states(job)) == ("succeeded", ["passed", "passed", "skipped", "passed"])
    assert run_git(repo, "log", "--format=%s").splitlines() == [EMPTY_COMMIT_MESSAGE]
    assert run_git(repo, "branch", "--show-current").strip() == "main"
    project = load_project("demo", projects_dir=projects_dir)
    assert project.commands.test is None
    assert project.tracker is not None and project.tracker.list_id == "9"
    yaml = parse((projects_dir / "demo" / "project.yaml").read_text(encoding="utf-8"))
    assert "commands" not in yaml


@pytest.mark.usefixtures("builtin_fixture")
@pytest.mark.parametrize("source", ["template", "existing", "empty"])
@pytest.mark.parametrize("step", STEP_NAMES)
def test_a_failure_after_any_step_leaves_only_what_existed(
    tmp_path: Path,
    projects_dir: Path,
    home: Path,
    git_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    source: str,
    step: str,
) -> None:
    original: Callable[[Runner], bool] = getattr(Runner, f"_{step}")

    def fail_after(self: Runner) -> bool:
        original(self)
        raise job_module._Failed("forced", "name", "forced output")

    monkeypatch.setattr(Runner, f"_{step}", fail_after)
    before, git_before = snapshot(tmp_path), git_state(git_repo)
    job = create(projects_dir, home, **source_fields(source, tmp_path, git_repo))
    assert job.state == "failed"
    failed = job.steps[STEP_NAMES.index(step)]
    assert (failed.state, failed.message, failed.field, failed.output) == (
        "failed",
        "forced",
        "name",
        "forced output",
    )
    assert all(s.state == "pending" for s in job.steps[STEP_NAMES.index(step) + 1 :])
    assert job.rollback is not None and job.rollback.left == []
    assert snapshot(tmp_path) == before
    assert git_state(git_repo) == git_before


@pytest.mark.parametrize("source", ["template", "empty"])
@pytest.mark.usefixtures("builtin_fixture")
def test_an_empty_folder_that_existed_survives_a_rollback(
    tmp_path: Path, projects_dir: Path, home: Path, monkeypatch: pytest.MonkeyPatch, source: str
) -> None:
    repo = tmp_path / "new"
    repo.mkdir()
    original = Runner._commit

    def fail_after(self: Runner) -> bool:
        original(self)
        raise job_module._Failed("forced", None)

    monkeypatch.setattr(Runner, "_commit", fail_after)
    job = create(projects_dir, home, **source_fields(source, tmp_path, tmp_path))
    assert job.state == "failed"
    assert repo.is_dir() and list(repo.iterdir()) == []
    assert not projects_dir.exists()


def test_a_failing_test_command_names_its_field(
    tmp_path: Path, projects_dir: Path, home: Path, git_repo: Path
) -> None:
    commands = {**PASS, "test": fake_tool_cmd("fail-test")}
    job = create(projects_dir, home, source="existing", repo_path=str(git_repo), commands=commands)
    assert job.state == "failed"
    assert states(job) == ["passed", "passed", "failed", "pending"]
    step = job.steps[2]
    assert (step.message, step.field) == ("The test command failed", "commands.test")
    assert step.output is not None
    assert "FAILED tests/test_math.py::test_add" in step.output
    assert not (projects_dir / "demo").exists()


@pytest.mark.usefixtures("isolated_git")
def test_a_commit_without_an_identity_fails_and_rolls_back(
    tmp_path: Path, projects_dir: Path, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for kind in ("AUTHOR", "COMMITTER"):
        monkeypatch.delenv(f"GIT_{kind}_NAME")
        monkeypatch.delenv(f"GIT_{kind}_EMAIL")
    job = create(projects_dir, home, source="empty", repo_path=str(tmp_path / "new"))
    step = job.steps[3]
    assert (job.state, step.state, step.field) == ("failed", "failed", "repo_path")
    assert step.message == "Couldn't make the initial commit"
    assert "user.name/user.email" in (step.output or "")
    assert not (tmp_path / "new").exists()
    assert job.rollback is not None
    assert str(tmp_path / "new") in job.rollback.removed


def test_cancel_during_check_commands_rolls_back(
    tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    jobs = jobs_for(projects_dir, home)
    commands = {"test": fake_tool_cmd("sleep")}
    request = CreateProject(
        name="demo", source="empty", repo_path=str(tmp_path / "new"), commands=commands
    )
    job_id = jobs.start(request).id
    deadline = time.monotonic() + 30
    while jobs.get(job_id).steps[2].state != "running":
        assert time.monotonic() < deadline
        time.sleep(0.05)
    cancelled = jobs.cancel(job_id)
    assert cancelled.state == "cancelled"
    assert cancelled.steps[2].state == "failed"
    assert cancelled.steps[2].message == "Cancelled"
    assert not (tmp_path / "new").exists()
    assert not projects_dir.exists()


def test_jobs_are_kept_for_an_hour(tmp_path: Path, projects_dir: Path, home: Path) -> None:
    now = [0.0]
    jobs = CreationJobs(
        projects_dir=projects_dir, worktrees_dir=home / "w", home=home, clock=lambda: now[0]
    )
    job = jobs.start(CreateProject(name="demo", source="empty", repo_path=str(tmp_path / "n")))
    jobs.wait(job.id, 60)
    ended = jobs.get(job.id).ended_at
    assert ended is not None
    now[0] = ended + 3_599
    assert jobs.get(job.id).state == "succeeded"
    now[0] = ended + 3_601
    with pytest.raises(UnknownJobError):
        jobs.get(job.id)


def test_rollback_never_follows_a_symlink(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("mine", encoding="utf-8")
    made = tmp_path / "made"
    made.mkdir()
    try:
        (made / "link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks need extra rights here")
    empty = tmp_path / "empty-before"
    empty.mkdir()
    (empty / "written").mkdir()
    (empty / "written" / "link").symlink_to(outside, target_is_directory=True)
    outcome = roll_back([(empty, "contents"), (made, "path")])
    assert outcome.left == []
    assert not made.exists()
    assert empty.is_dir() and list(empty.iterdir()) == []
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "mine"
