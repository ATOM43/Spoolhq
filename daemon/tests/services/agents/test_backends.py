from spoolhq.services.agents import (
    ClaudeCliRunner,
    CodexCliRunner,
    available_runners,
    backend_names,
    make_runner,
)


def test_the_built_in_backends() -> None:
    assert backend_names() == ("claude-code-cli", "codex-cli")
    runners = available_runners()
    assert [runner.name for runner in runners] == ["claude-code-cli", "codex-cli"]
    assert isinstance(runners[0], ClaudeCliRunner)
    assert isinstance(runners[1], CodexCliRunner)


def test_codex_takes_the_endpoint_and_model() -> None:
    runner = make_runner("codex-cli", base_url="http://localhost:11434/v1", model="qwen3-coder")
    assert isinstance(runner, CodexCliRunner)
    assert (runner.base_url, runner.model) == ("http://localhost:11434/v1", "qwen3-coder")
