"""A model per role: the format, precedence, validation and what reaches the CLI."""

from pathlib import Path

import pytest

from spoolhq.services.agents.claude_config import build_argv
from spoolhq.services.agents.model import AgentPolicy, Budget
from spoolhq.services.projects import load_project, parse_project, save_project
from tests.services.projects.test_workspace import valid_data, write_project

PLAIN = """\
name: demo   # mine
repo: {repo}
agents:
  default: claude-code-cli
  reviewer: codex-cli        # a second opinion
  backends:
    claude-code-cli:
      model: qwen3-coder     # the backend's default
"""


def test_plain_role_names_load_and_save_byte_identically(
    projects_dir: Path, git_repo: Path
) -> None:
    path = write_project(projects_dir, PLAIN.format(repo=git_repo))
    before = path.read_bytes()
    project = load_project("demo", projects_dir=projects_dir)
    assert project.agents.backend_for("reviewer") == "codex-cli"
    save_project(project, projects_dir=projects_dir)
    assert path.read_bytes() == before
    dumped = project.model_dump(mode="json", exclude_unset=True)["agents"]
    assert dumped["reviewer"] == "codex-cli"


def test_role_mapping_round_trips_and_only_roles_with_a_model_are_mappings(
    projects_dir: Path, git_repo: Path
) -> None:
    data = valid_data(git_repo)
    data["agents"] = {
        "planner": {"backend": "default", "model": "claude-opus-x"},
        "implementer": {"model": "claude-sonnet-x.y"},
        "reviewer": {"backend": "codex-cli"},
    }
    agents = parse_project("demo", data).model_dump(mode="json", exclude_unset=True)["agents"]
    assert agents == {
        "planner": {"backend": "default", "model": "claude-opus-x"},
        "implementer": {"model": "claude-sonnet-x.y"},
        "reviewer": "codex-cli",
    }


def test_role_model_beats_backend_model_beats_the_default(git_repo: Path) -> None:
    data = valid_data(git_repo)
    data["agents"] = {
        "planner": {"backend": "default", "model": "big"},
        "reviewer": "codex-cli",
        "backends": {"claude-code-cli": {"model": "small"}},
    }
    agents = parse_project("demo", data).agents
    assert agents.model_for("planner") == ("big", "role")
    assert agents.model_for("implementer") == ("small", "backend")
    assert agents.model_for("reviewer") == (None, "default")


def test_two_roles_on_one_backend_get_their_own_model_on_the_command_line(
    git_repo: Path, home: Path
) -> None:
    data = valid_data(git_repo)
    data["agents"] = {
        "planner": {"model": "claude-opus-x"},
        "implementer": {"backend": "claude-code-cli", "model": "claude-haiku-x"},
    }
    agents = parse_project("demo", data).agents
    budget = Budget(max_turns=5, max_usd=None, max_tokens=None)
    policy = AgentPolicy.for_worktree(git_repo, {"test": "just test"}, home)
    for role, model in (("planner", "claude-opus-x"), ("implementer", "claude-haiku-x")):
        runner = agents.runner_for(role)  # type: ignore[arg-type]
        assert runner.name == "claude-code-cli"
        argv = build_argv([], policy, budget, billing="subscription", model=runner.model)  # type: ignore[attr-defined]
        assert argv[argv.index("--model") + 1] == model


@pytest.mark.parametrize(
    "model", ["claude-sonnet-x.y", "qwen2.5-coder:7b", "org/model_1", "x" * 100]
)
def test_good_model_names_pass(git_repo: Path, model: str) -> None:
    data = valid_data(git_repo)
    data["agents"] = {"reviewer": {"backend": "codex-cli", "model": model}}
    assert parse_project("demo", data).agents.model_for("reviewer") == (model, "role")
