"""`spool agents`: which agent backends are installed and usable."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import agents as agents_cli
from spoolhq.cli import app
from spoolhq.services.agents import AgentRunner, BackendInfo, ClaudeCliRunner, CodexCliRunner
from spoolhq.services.projects import BackendSettings, load_project, save_project
from tests.conftest import (
    AGENT_FIXTURES,
    CODEX_FIXTURES,
    FakeBackend,
    fake_claude_cmd,
    fake_codex_cmd,
    sandbox_which,
)

runner = CliRunner()


def use(monkeypatch: pytest.MonkeyPatch, agent: AgentRunner) -> None:
    monkeypatch.setattr(agents_cli, "available_runners", lambda: [agent])


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


@pytest.mark.integration
def test_codex_shows_what_it_enforces_per_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cmd = fake_codex_cmd(CODEX_FIXTURES / "success_writes_file.jsonl", tmp_path / "rec.json")
    codex = CodexCliRunner(
        codex_cmd=cmd,
        platform="win32",
        which=sandbox_which,
        system_config=tmp_path / "none.toml",
    )
    use(monkeypatch, codex)
    result = runner.invoke(app, ["agents"])
    assert result.exit_code == 0, result.output
    lines = result.output.splitlines()
    assert lines[:3] == [
        "codex-cli",
        "  installed  yes (0.166.0)",
        "  login      yes (chatgpt, subscription)",
    ]
    assert lines[3].startswith("  policy     no: Codex's deny rules for credential files")
    assert lines[4:] == [
        "  planner      read-only yes, approvals never asked yes, network off yes, "
        "denied reads no, the shell allowlist no",
        "  implementer  writes confined to the worktree yes, approvals never asked yes, "
        "network off yes, denied reads no, the shell allowlist no",
        "  reviewer     read-only yes, approvals never asked yes, network off yes, "
        "denied reads no, the shell allowlist no",
        "  warning    as reviewer or planner it can run read-only shell commands",
    ]


def test_codex_not_logged_in_says_codex_login() -> None:
    info = BackendInfo(
        name="codex-cli",
        installed=True,
        version="0.166.0",
        logged_in=False,
        auth_method=None,
        billing="unknown",
        policy_enforceable=True,
        reason="Codex CLI is not logged in; run: codex login",
    )
    assert agents_cli.describe(info)[2] == "  login      no (run: codex login)"


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


def test_project_warns_about_a_codex_reviewer(workspace: Path, projects_dir: Path) -> None:
    settings = load_project("demo", projects_dir=projects_dir)
    agents = settings.agents.model_copy(update={"reviewer": "codex-cli"})
    save_project(settings.model_copy(update={"agents": agents}), projects_dir=projects_dir)
    result = runner.invoke(app, ["agents", "--project", "demo"])
    assert result.exit_code == 0, result.output
    assert result.stdout.splitlines()[2].startswith("reviewer     codex-cli")
    assert result.stderr.splitlines() == [
        "warning: the reviewer uses codex-cli, which can run read-only shell commands "
        "(Claude Code's has no shell)"
    ]


def test_unknown_project_fails() -> None:
    result = runner.invoke(app, ["agents", "--project", "nope"])
    assert result.exit_code == 1
    assert "nope" in result.output
