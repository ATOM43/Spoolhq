from spoolhq.services.agents import ClaudeCliRunner, available_runners


def test_claude_code_cli_is_the_only_backend() -> None:
    runners = available_runners()
    assert [runner.name for runner in runners] == ["claude-code-cli"]
    assert isinstance(runners[0], ClaudeCliRunner)
