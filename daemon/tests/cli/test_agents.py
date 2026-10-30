"""`spool agents`: which agent backends are installed and usable."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import agents as agents_cli
from spoolhq.cli import app
from spoolhq.services.agents import BackendInfo, ClaudeCliRunner
from spoolhq.services.projects import BackendSettings, load_project, save_project
from tests.conftest import AGENT_FIXTURES, FakeBackend, fake_claude_cmd, sandbox_which

runner = CliRunner()


def use(monkeypatch: pytest.MonkeyPatch, claude: ClaudeCliRunner) -> None:
    monkeypatch.setattr(agents_cli, "available_runners", lambda: [claude])


@pytest.mark.integration
def test_lists_the_installed_backend(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cmd = fake_claude_cmd(AGENT_FIXTURES / "success_writes_file.jsonl", tmp_path / "rec.json")
    use(monkeypatch, ClaudeCliRunner(claude_cmd=cmd, platform="linux", which=sandbox_which))
    result = runner.invoke(app, ["agents"])
    assert result.exit_code == 0, result.output
    assert result.output == (
        "claude-code-cli\n"
        "  installed  yes (2.1.302)\n"
        "  login      yes (claude.ai, subscription)\n"
        "  policy     yes (enforceable)\n"
    )


def test_nothing_installed_says_how_to_install(monkeypatch: pytest.MonkeyPatch) -> None:
    use(monkeypatch, ClaudeCliRunner(which=lambda name: None))
    result = runner.invoke(app, ["agents"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[:2] == ["claude-code-cli", "  installed  no"]
    assert "https://code.claude.com/docs/en/setup" in lines[2]
    assert "claude auth login" in lines[2]


def test_not_logged_in_and_not_enforceable() -> None:
    info = BackendInfo(
        name="claude-code-cli",
        installed=True,
        version="2.1.302",
        logged_in=False,
        auth_method="none",
        billing="unknown",
        policy_enforceable=False,
        reason="run SpoolHQ inside WSL2",
    )
    assert agents_cli.describe(info) == [
        "claude-code-cli",
        "  installed  yes (2.1.302)",
        "  login      no (run: claude auth login)",
        "  policy     no: run SpoolHQ inside WSL2",
    ]


def test_backends_are_separated_by_a_blank_line(monkeypatch: pytest.MonkeyPatch) -> None:
    missing = ClaudeCliRunner(which=lambda name: None)
    monkeypatch.setattr(agents_cli, "available_runners", lambda: [missing, missing])
    result = runner.invoke(app, ["agents"])
    assert result.output.splitlines()[3:5] == ["", "claude-code-cli"]


def test_project_shows_each_roles_backend_model_and_endpoint(
    workspace: Path, projects_dir: Path, fake_backend: FakeBackend
) -> None:
    fake_backend("fake-reviewer", ClaudeCliRunner())
    settings = load_project("demo", projects_dir=projects_dir)
    agents = settings.agents.model_copy(
        update={
            "reviewer": "fake-reviewer",
            "backends": {
                "claude-code-cli": BackendSettings(
                    base_url="http://localhost:11434", model="qwen3-coder"
                )
            },
        }
    )
    save_project(settings.model_copy(update={"agents": agents}), projects_dir=projects_dir)
    result = runner.invoke(app, ["agents", "--project", "demo"])
    assert result.exit_code == 0, result.output
    assert result.output.splitlines() == [
        "planner      claude-code-cli  model: qwen3-coder  endpoint: http://localhost:11434",
        "implementer  claude-code-cli  model: qwen3-coder  endpoint: http://localhost:11434",
        "reviewer     fake-reviewer  model: default  endpoint: default",
    ]


def test_unknown_project_fails() -> None:
    result = runner.invoke(app, ["agents", "--project", "nope"])
    assert result.exit_code == 1
    assert "nope" in result.output
