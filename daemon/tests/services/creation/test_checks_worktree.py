"""An existing repo's commands run in a temporary worktree, never in the user's checkout."""

import shlex
import shutil
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.devtools import dev_agents
from spoolhq.services.creation import CreateProject, CreationJobs, Job
from spoolhq.services.creation.job import BASELINE_MESSAGE, CHECKS_WORKTREE
from spoolhq.services.git import WorktreeManager, ensure_clean, recover_worktrees
from tests.conftest import REVIEW_FIXTURES, fake_tool_cmd, run_git, set_identity
from tests.devtools.test_fake_runner import run_next

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("git_identity")]

PASS = fake_tool_cmd("pass")
# Imports a module of the repo (writing __pycache__ next to it) and drops a marker file.
CHECK_SCRIPT = """\
import os, sys
sys.path.insert(0, os.getcwd())
open("ran-here", "w").close()
import pkg
raise SystemExit(0 if pkg.ok() else 1)
"""


@pytest.fixture
def python_repo(git_repo: Path, tmp_path: Path) -> Path:
    """``git_repo`` with a Python module and no ``.gitignore``, committed."""
    (git_repo / "pkg.py").write_text("def ok():\n    return True\n", encoding="utf-8")
    set_identity(git_repo)
    run_git(git_repo, "add", "pkg.py")
    run_git(git_repo, "commit", "--quiet", "-m", "add pkg")
    return git_repo


def check_command(tmp_path: Path) -> str:
    script = tmp_path / "check.py"
    script.write_text(CHECK_SCRIPT, encoding="utf-8")
    return shlex.join([Path(sys.executable).as_posix(), script.as_posix()])


def jobs_for(projects_dir: Path, home: Path) -> CreationJobs:
    return CreationJobs(projects_dir=projects_dir, worktrees_dir=home / "worktrees", home=home)


def request(repo: Path, test: str) -> CreateProject:
    commands = {"install": PASS, "lint": PASS, "test": test}
    return CreateProject(name="demo", source="existing", repo_path=str(repo), commands=commands)


def assert_no_checks_worktree(repo: Path, home: Path) -> None:
    assert not (home / "worktrees" / "demo" / CHECKS_WORKTREE).exists()
    listed = run_git(repo, "worktree", "list", "--porcelain").count("worktree ")
    assert listed == 1


def test_checks_leave_the_checkout_untouched(
    python_repo: Path, tmp_path: Path, projects_dir: Path, home: Path
) -> None:
    jobs = jobs_for(projects_dir, home)
    job = jobs.wait(jobs.start(request(python_repo, check_command(tmp_path))).id, 60)
    assert job.state == "succeeded", job.steps
    assert run_git(python_repo, "status", "--porcelain", "--ignored") == ""
    assert not (python_repo / "__pycache__").exists()
    assert not (python_repo / "ran-here").exists()
    ensure_clean(python_repo)  # what the first run checks
    assert_no_checks_worktree(python_repo, home)


@pytest.mark.parametrize("test", ["fail-test", "lint-error"])
def test_a_failing_baseline_is_the_repos_own_failure(
    python_repo: Path, projects_dir: Path, home: Path, test: str
) -> None:
    jobs = jobs_for(projects_dir, home)
    command = fake_tool_cmd(test)
    job = jobs.wait(jobs.start(request(python_repo, command)).id, 60)
    step = job.steps[2]
    assert (job.state, step.state, step.field) == ("failed", "failed", "commands.test")
    assert step.message == BASELINE_MESSAGE.format(command=command)
    assert step.message.startswith("Your tests fail before any change: ")
    assert step.output
    assert_no_checks_worktree(python_repo, home)
    assert run_git(python_repo, "status", "--porcelain", "--ignored") == ""


def test_cancel_removes_the_checks_worktree(
    python_repo: Path, projects_dir: Path, home: Path
) -> None:
    jobs = jobs_for(projects_dir, home)
    job_id = jobs.start(request(python_repo, fake_tool_cmd("sleep"))).id
    deadline = time.monotonic() + 30
    while jobs.get(job_id).steps[2].passed != ["install", "lint"]:
        assert time.monotonic() < deadline
        time.sleep(0.05)
    assert (home / "worktrees" / "demo" / CHECKS_WORKTREE).is_dir()
    cancelled: Job = jobs.cancel(job_id)
    assert cancelled.state == "cancelled"
    assert_no_checks_worktree(python_repo, home)


def test_startup_cleanup_removes_a_crashed_checks_worktree(git_repo: Path, home: Path) -> None:
    path = home / "worktrees" / "demo" / CHECKS_WORKTREE
    run_git(git_repo, "worktree", "add", "--detach", "--quiet", str(path), "HEAD")
    manager = WorktreeManager(git_repo, "demo", "main", home / "worktrees")
    report = recover_worktrees(manager, lambda _: False)
    assert report.removed == [CHECKS_WORKTREE]
    assert_no_checks_worktree(git_repo, home)


def test_the_first_run_starts_on_a_repo_created_from_existing(
    python_repo: Path, tmp_path: Path, projects_dir: Path, home: Path, token: str
) -> None:
    """The T42 bug: checks in the checkout left __pycache__ and the first run refused."""
    jobs = jobs_for(projects_dir, home)
    command = check_command(tmp_path)
    assert jobs.wait(jobs.start(request(python_repo, command)).id, 60).state == "succeeded"
    tickets = projects_dir / "demo" / "tickets"
    shutil.copy(REVIEW_FIXTURES / "T07-parse-slug.md", tickets / "T07-parse-slug.md")
    settings = load_settings()
    app = create_app(settings, token=token, agents=dev_agents("happy", delay_s=0))
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as client:
        current = run_next(client, token)
    assert current["run"]["status"] == "done", current
