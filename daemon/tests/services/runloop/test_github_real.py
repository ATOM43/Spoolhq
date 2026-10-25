"""Opt-in: direct delivery and one pull request against a real, throwaway GitHub repo.

Skipped unless ``SPOOLHQ_GITHUB_TEST_REPO`` (``https://github.com/<owner>/<repo>``, a
repository you can push to and whose default branch is ``main``) and a token
(``SPOOLHQ_GITHUB_TEST_TOKEN``) are set; git must be able to push there with your own
credential helper or SSH agent. It pushes a commit to ``main``, opens a pull request
and closes it again.
"""

import os
from pathlib import Path

import pytest

from spoolhq.services.agents import FakeRunner
from spoolhq.services.git import github_repo
from spoolhq.services.github import GitHubClient
from spoolhq.services.projects import load_project, save_project
from spoolhq.services.runloop import Delivery, GitHubPoller
from spoolhq.services.runs import RunRegistry, RunStatus
from spoolhq.services.tickets import load_ticket, save_ticket
from tests.conftest import run_git
from tests.services.runloop.conftest import LoopFactory, ManualClock, Transcripts

REPO = os.environ.get("SPOOLHQ_GITHUB_TEST_REPO", "")
TOKEN = os.environ.get("SPOOLHQ_GITHUB_TEST_TOKEN", "")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not (REPO and TOKEN), reason="set SPOOLHQ_GITHUB_TEST_REPO and _TOKEN"),
]


def test_direct_push_and_a_pull_request_on_github(
    make_loop: LoopFactory,
    transcripts: Transcripts,
    clock: ManualClock,
    registry: RunRegistry,
    repo: Path,
    projects_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", TOKEN)
    # Your own git setup (credential helper, SSH agent), which `repo` otherwise hides.
    monkeypatch.delenv("GIT_CONFIG_GLOBAL")
    monkeypatch.delenv("GIT_CONFIG_NOSYSTEM")
    settings = load_project("demo", projects_dir=projects_dir)
    settings.git.remote = REPO
    save_project(settings, projects_dir=projects_dir)
    # Start from the remote's main, so local main has nothing the remote lacks.
    run_git(repo, "fetch", "--quiet", REPO, "main")
    run_git(repo, "reset", "--quiet", "--hard", "FETCH_HEAD")
    for tid in ("T01", "T02"):  # tags from an earlier run of this test would clash
        tag = f"refs/tags/ticket/{tid}"
        if run_git(repo, "ls-remote", REPO, tag).strip():
            run_git(repo, "push", "--quiet", REPO, f":{tag}")
    ticket = load_ticket("demo", "T02", projects_dir=projects_dir)
    ticket.meta.review_required = True
    save_ticket("demo", ticket, projects_dir=projects_dir)

    implement = [transcripts.implement({f"spool_{n}.txt": f"{n}\n"}) for n in (1, 2)]
    loop, _ = make_loop(
        FakeRunner(implement),
        [transcripts.review("approve")] * 2,
        integrator=Delivery(clock=clock),
    )
    loop.start("demo", "next", "T01")
    loop.wait("demo")
    run_log = registry.get("demo").run_log
    assert run_log.list_runs()[0].status is RunStatus.DONE, run_log.list_runs()[0].reason

    loop.start("demo", "next", "T02")
    loop.wait("demo")
    run = run_log.list_runs()[0]
    assert run.pr_number is not None, run.reason
    assert GitHubPoller(loop, registry).sync("demo") == [f"T02: PR #{run.pr_number} open"]
    with GitHubClient(TOKEN) as client:
        client.request(
            "PATCH", f"/repos/{github_repo(REPO)}/pulls/{run.pr_number}", json={"state": "closed"}
        )
    assert GitHubPoller(loop, registry).sync("demo") == [
        f"T02: blocked, PR #{run.pr_number} was closed without merging"
    ]
