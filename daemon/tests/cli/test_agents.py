"""`spool agents`: which agent backends are installed and usable."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from spoolhq.cli import agents as agents_cli
from spoolhq.cli import app
from spoolhq.services.agents import BackendInfo, ClaudeCliRunner
from tests.conftest import AGENT_FIXTURES, fake_claude_cmd, sandbox_which

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
