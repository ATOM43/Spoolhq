from spoolhq.services.agents import (
    AgentSdkRunner,
    ClaudeCliRunner,
    CodexCliRunner,
    available_runners,
    backend_names,
    make_runner,
)


def test_the_built_in_backends() -> None:
    assert backend_names() == ("claude-code-cli", "codex-cli", "claude-agent-sdk")
    runners = available_runners()
    assert [runner.name for runner in runners] == list(backend_names())
    assert isinstance(runners[0], ClaudeCliRunner)
    assert isinstance(runners[1], CodexCliRunner)
    assert isinstance(runners[2], AgentSdkRunner)


def test_the_agent_sdk_takes_the_endpoint_and_model() -> None:
    runner = make_runner("claude-agent-sdk", base_url="http://localhost:11434", model="qwen3")
    assert isinstance(runner, AgentSdkRunner)
    assert (runner.base_url, runner.model) == ("http://localhost:11434", "qwen3")


def test_codex_takes_the_endpoint_and_model() -> None:
    runner = make_runner("codex-cli", base_url="http://localhost:11434/v1", model="qwen3-coder")
    assert isinstance(runner, CodexCliRunner)
    assert (runner.base_url, runner.model) == ("http://localhost:11434/v1", "qwen3-coder")
