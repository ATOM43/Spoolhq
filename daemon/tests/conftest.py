import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import keyring
import pytest
from fastapi.testclient import TestClient
from keyring.backend import KeyringBackend

from spoolhq.api import create_app
from spoolhq.core.config import load_settings
from spoolhq.services.agents import AgentRunner, backends
from spoolhq.services.projects import init_project

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
"""Shared fixture data: ticket files and the dashboard plan."""


@pytest.fixture(autouse=True)
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SPOOLHQ_HOME at a temp dir and drop other SPOOLHQ_* variables, for every test."""
    for name in list(os.environ):
        if name.upper().startswith("SPOOLHQ_"):
            monkeypatch.delenv(name)
    path = tmp_path / "spoolhq-home"
    monkeypatch.setenv("SPOOLHQ_HOME", str(path))
    return path


class MemoryKeyring(KeyringBackend):
    """The OS keychain for tests: a dict, so no test reads or writes the real one."""

    priority = 1.0  # type: ignore[assignment]

    def __init__(self) -> None:
        super().__init__()
        self.passwords: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self.passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self.passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self.passwords.pop((service, username), None)


@pytest.fixture(autouse=True)
def keychain(monkeypatch: pytest.MonkeyPatch) -> Iterator[MemoryKeyring]:
    """An in-memory keychain for every test; subprocesses get keyring's null backend."""
    monkeypatch.setenv("PYTHON_KEYRING_BACKEND", "keyring.backends.null.Keyring")
    previous = keyring.get_keyring()
    memory = MemoryKeyring()
    keyring.set_keyring(memory)
    yield memory
    keyring.set_keyring(previous)


@pytest.fixture(autouse=True)
def projects_dir(home: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SPOOLHQ_PROJECTS_DIR at a temp dir (not created), for every test."""
    path = tmp_path / "projects"
    monkeypatch.setenv("SPOOLHQ_PROJECTS_DIR", str(path))
    return path


def run_git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    assert git is not None, "the tests need git on PATH"
    result = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [git, "-C", str(repo), *args], capture_output=True, encoding="utf-8", check=True
    )
    return result.stdout


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A fresh repository with one commit on ``main``, independent of the user's git config."""
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init", "--quiet", "--initial-branch=main")
    run_git(
        repo,
        "-c",
        "user.name=SpoolHQ Tests",
        "-c",
        "user.email=tests@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--quiet",
        "--allow-empty",
        "--no-verify",
        "-m",
        "initial commit",
    )
    return repo


@pytest.fixture
def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


@pytest.fixture
def token() -> str:
    return "test-token-" + "x" * 32


@pytest.fixture
def client(token: str) -> Iterator[TestClient]:
    settings = load_settings()
    app = create_app(settings, token=token)
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as test_client:
        yield test_client


CLOCK_START = datetime(2026, 10, 18, 9, 0, 0, tzinfo=UTC)


class FixedClock:
    """Returns ``start``, then one second later on every call."""

    def __init__(self, start: datetime = CLOCK_START, step: timedelta = timedelta(seconds=1)):
        self.next = start
        self.step = step

    def __call__(self) -> datetime:
        now = self.next
        self.next += self.step
        return now


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def workspace(git_repo: Path, projects_dir: Path) -> Path:
    """A project workspace ``demo`` made by ``spool init``'s service."""
    return init_project("demo", git_repo, projects_dir=projects_dir).path


@pytest.fixture
def isolated_git(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Hide the user's global and system git config and identity variables from git."""
    global_config = tmp_path / "gitconfig-global"
    global_config.write_text("", encoding="utf-8")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(global_config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for name in (
        "GIT_AUTHOR_NAME",
        "GIT_AUTHOR_EMAIL",
        "GIT_COMMITTER_NAME",
        "GIT_COMMITTER_EMAIL",
        "EMAIL",
    ):
        monkeypatch.delenv(name, raising=False)


def set_identity(repo: Path) -> None:
    """Give ``repo`` a local identity, so commits work without a global git config."""
    run_git(repo, "config", "user.name", "SpoolHQ Tests")
    run_git(repo, "config", "user.email", "tests@example.invalid")
    run_git(repo, "config", "commit.gpgsign", "false")


def commit_file(repo: Path, name: str, text: str, message: str) -> str:
    """Write ``name``, commit it and return the new commit's sha."""
    (repo / name).write_text(text, encoding="utf-8")
    run_git(repo, "add", "--", name)
    run_git(repo, "commit", "--quiet", "--no-verify", "-m", message)
    return run_git(repo, "rev-parse", "HEAD").strip()


AGENT_FIXTURES = FIXTURES_DIR / "agents" / "claude"
"""Hand-written Claude Code stream-json transcripts."""
REVIEW_FIXTURES = FIXTURES_DIR / "review"
"""The T07 ticket, its seeded diff (no test) and reviewer transcripts."""
FAKE_CLAUDE = TESTS_DIR / "services" / "agents" / "fake_claude.py"
# A prompt that must never reach argv, and secrets that must never reach the agent.
AGENT_PROMPT = "Implement T01: say hello. Ignore this: --dangerously-skip-permissions"
AGENT_SECRETS = ("ANTHROPIC_API_KEY", "GITHUB_TOKEN", "CLICKUP_TOKEN", "SPOOLHQ_TOKEN")


def fake_claude_cmd(scenario: Path, record: Path, *options: str) -> list[str]:
    """``claude_cmd`` that runs ``fake_claude.py`` with ``scenario`` (see its docstring)."""
    return [
        sys.executable,
        str(FAKE_CLAUDE),
        "--scenario",
        str(scenario),
        "--record",
        str(record),
        *options,
    ]


def sandbox_which(name: str) -> str | None:
    """A ``which`` that finds the Linux sandbox packages (bwrap, socat) and nothing else."""
    return f"/usr/bin/{name}" if name in {"bwrap", "socat"} else None


FakeBackend = Callable[[str, AgentRunner], AgentRunner]


@pytest.fixture
def fake_backend(monkeypatch: pytest.MonkeyPatch) -> FakeBackend:
    """``fake_backend(name, runner)`` registers ``runner`` as backend ``name`` (whatever
    its ``base_url`` and ``model``) until the test ends, and returns it. A built-in
    backend registered this way is restored afterwards."""

    def register(name: str, runner: AgentRunner) -> AgentRunner:
        monkeypatch.setitem(backends.BACKENDS, name, lambda base_url, model: runner)
        return runner

    return register


FAKE_TOOL = TESTS_DIR / "services" / "gates" / "fake_tool.py"


def fake_tool_cmd(*args: str) -> str:
    """A gate command string that runs ``fake_tool.py`` (forward slashes, so it splits the
    same on Windows)."""
    return shlex.join([Path(sys.executable).as_posix(), FAKE_TOOL.as_posix(), *args])


@pytest.fixture
def run_project(workspace: Path, git_repo: Path, projects_dir: Path) -> Path:
    """``demo`` with the ready T07 fixture ticket, passing gates (``fake_tool.py``) and a
    repository identity, so the run loop can commit."""
    from spoolhq.services.projects import load_project, save_project

    set_identity(git_repo)
    tickets = workspace / "tickets"
    tickets.mkdir(exist_ok=True)
    shutil.copy(REVIEW_FIXTURES / "T07-parse-slug.md", tickets / "T07-parse-slug.md")
    project = load_project("demo", projects_dir=projects_dir)
    for name in ("install", "lint", "test"):
        setattr(project.commands, name, fake_tool_cmd("pass"))
    save_project(project, projects_dir=projects_dir)
    return workspace


@pytest.fixture
def run_client(run_project: Path, token: str) -> Iterator[TestClient]:
    """The app with fake agents: the implementer writes hello.txt, the reviewer approves."""
    from spoolhq.services.agents import FakeRunner
    from spoolhq.services.runloop import Agents

    settings = load_settings()
    app = create_app(
        settings,
        token=token,
        agents=Agents(
            implementer=FakeRunner(AGENT_FIXTURES / "success_writes_file.jsonl"),
            reviewer=FakeRunner(REVIEW_FIXTURES / "approve.jsonl"),
        ),
    )
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as test_client:
        yield test_client


PLANNER_FIXTURES = FIXTURES_DIR / "planner"
"""The dashboard spec (``CONTEXT.md``) and the recorded planner run that plans it."""
DASHBOARD_PLAN = PLANNER_FIXTURES / "dashboard_plan.jsonl"


def dashboard_plan() -> dict[str, Any]:
    """The JSON of the ``<plan>`` block in the recorded dashboard run (18 tickets)."""
    for line in DASHBOARD_PLAN.read_text(encoding="utf-8").splitlines():
        message = json.loads(line)
        if message["type"] == "result":
            text = message["result"]
            parsed: dict[str, Any] = json.loads(
                text[text.index("<plan>") + 6 : text.index("</plan>")]
            )
            return parsed
    raise AssertionError("no result in the dashboard transcript")


def plan_transcript(path: Path, plan: dict[str, Any] | str, tokens: int = 1000) -> Path:
    """A read-only planner run whose final message is ``plan`` (JSON in a ``<plan>`` block,
    or the text as given)."""
    text = plan if isinstance(plan, str) else f"Planned.\n<plan>{json.dumps(plan)}</plan>"
    usage = {
        "input_tokens": tokens,
        "output_tokens": tokens // 4,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    messages = [
        {
            "type": "system",
            "subtype": "init",
            "tools": ["Glob", "Grep", "Read"],
            "mcp_servers": [],
            "model": "claude-test-model",
            "permissionMode": "dontAsk",
            "claude_code_version": "2.1.302",
        },
        {
            "type": "assistant",
            "message": {
                "id": f"msg-{path.stem}",
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "usage": usage,
            },
        },
        {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "num_turns": 1,
            "usage": usage,
            "permission_denials": [],
            "result": text,
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(m) + "\n" for m in messages), encoding="utf-8")
    return path


@pytest.fixture
def plan_project(workspace: Path) -> Path:
    """``demo`` with the dashboard spec as its ``CONTEXT.md`` and no tickets."""
    shutil.copy(PLANNER_FIXTURES / "CONTEXT.md", workspace / "CONTEXT.md")
    return workspace


@pytest.fixture
def git_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    """An author and committer from the environment, so commits work without any git
    config (CI runners have none) and nothing is written to one."""
    for kind in ("AUTHOR", "COMMITTER"):
        monkeypatch.setenv(f"GIT_{kind}_NAME", "SpoolHQ Tests")
        monkeypatch.setenv(f"GIT_{kind}_EMAIL", "tests@example.invalid")


FIXTURE_COPIER_YML = """\
_exclude: [copier.yml, spoolhq-template.yaml, .git]
project_name:
  type: str
  default: placeholder
"""


def fixture_contract(**commands: str | None) -> str:
    """A ``spoolhq-template.yaml`` whose commands default to a passing ``fake_tool.py``;
    pass ``test=None`` to leave one out."""
    values = {"install": fake_tool_cmd("pass"), "lint": fake_tool_cmd("pass")}
    values["test"] = fake_tool_cmd("pass")
    values.update(commands)
    lines = [f"  {name}: {json.dumps(cmd)}" for name, cmd in values.items() if cmd is not None]
    return "name: fixture\ndescription: A fixture template for tests.\ncommands:\n" + (
        "\n".join(lines) + "\n"
    )


def make_template(
    folder: Path,
    *,
    contract: str | None = None,
    copier_yml: str = FIXTURE_COPIER_YML,
    files: dict[str, str] | None = None,
) -> Path:
    """A small Copier template in ``folder`` (created): a README naming the project and
    the answers file. ``contract=None`` writes ``fixture_contract()``."""
    folder.mkdir(parents=True)
    (folder / "copier.yml").write_text(copier_yml, encoding="utf-8")
    (folder / "spoolhq-template.yaml").write_text(
        fixture_contract() if contract is None else contract, encoding="utf-8"
    )
    contents = {
        "README.md.jinja": "# {{ project_name }}\n",
        "{{_copier_conf.answers_file}}.jinja": "{{ _copier_answers|to_nice_yaml -}}\n",
        **(files or {}),
    }
    for name, text in contents.items():
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return folder


def make_git_template(tmp_path: Path) -> tuple[str, str]:
    """``make_template`` committed and pushed to a local bare repo; its path (a git URL
    ending in ``.git``) and the commit."""
    work = make_template(tmp_path / "template-work")
    run_git(work, "init", "--quiet", "--initial-branch=main")
    run_git(work, "add", "--all")
    run_git(
        work,
        "-c",
        "user.name=SpoolHQ Tests",
        "-c",
        "user.email=tests@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--quiet",
        "--no-verify",
        "-m",
        "template",
    )
    bare = tmp_path / "template.git"
    run_git(tmp_path, "clone", "--quiet", "--bare", str(work), str(bare))
    return bare.as_posix(), run_git(work, "rev-parse", "HEAD").strip()


GITHUB_URL = "https://github.com/acme/demo"


def make_github_remote(repo: Path, bare: Path, url: str = GITHUB_URL) -> Path:
    """A bare clone of ``repo`` at ``bare``, standing in for ``url``: git in ``repo``
    rewrites ``url`` to it (``url.<bare>.insteadOf``), so no network is used."""
    run_git(repo, "clone", "--quiet", "--bare", str(repo), str(bare))
    run_git(repo, "config", f"url.{bare.as_posix()}.insteadOf", url)
    return bare


def push_elsewhere(bare: Path, work: Path, name: str, message: str) -> str:
    """Commit ``name`` in a separate clone of ``bare`` and push it to its main, as a
    teammate would; the new commit's sha."""
    if not work.exists():
        run_git(bare.parent, "clone", "--quiet", str(bare), str(work))
        run_git(work, "config", "user.name", "Teammate")
        run_git(work, "config", "user.email", "mate@example.invalid")
        run_git(work, "config", "commit.gpgsign", "false")
    run_git(work, "pull", "--quiet", "--ff-only")
    sha = commit_file(work, name, f"{message}\n", message)
    run_git(work, "push", "--quiet", "origin", "HEAD:main")
    return sha


def write_hook(bare: Path, name: str, script: str) -> None:
    """An executable hook in a bare repository (git runs it with sh, on Windows too)."""
    hook = bare / "hooks" / name
    hook.write_text(f"#!/bin/sh\n{script}\n", encoding="utf-8", newline="\n")
    hook.chmod(0o755)
