"""Splitting gate commands without a shell, and the gate environment."""

import pytest

from spoolhq.services.gates import SHELL_SYNTAX_ERROR, gate_env, split_command


@pytest.mark.parametrize(
    "command",
    [
        "just test && rm -rf /",
        "just test | tee x",
        "echo `id`",
        "just test || true",
        "just test; rm x",
        "just test > out",
        "just test < in",
        "echo $(id)",
    ],
)
def test_shell_syntax_is_refused(command: str) -> None:
    with pytest.raises(ValueError, match=SHELL_SYNTAX_ERROR):
        split_command(command)


def test_quoted_argument_with_spaces_is_one_argument() -> None:
    assert split_command('pytest -k "adds two numbers" tests') == [
        "pytest",
        "-k",
        "adds two numbers",
        "tests",
    ]


def test_unclosed_quote_is_refused() -> None:
    with pytest.raises(ValueError, match="can't be split into arguments: No closing quotation"):
        split_command('pytest -k "oops')


def test_gate_env_drops_secrets_and_adds_ci_settings() -> None:
    parent = {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "ANTHROPIC_API_KEY": "sk",
        "GITHUB_TOKEN": "gh",
        "MY_SECRET": "s",
        "CLICKUP_API_KEY": "c",
        "DB_PASSWORD": "p",
        "LC_ALL": "C.UTF-8",
        "FORCE_COLOR": "1",
    }

    env = gate_env(parent, platform="linux")

    assert env == {
        "PATH": "/usr/bin",
        "HOME": "/home/me",
        "LC_ALL": "C.UTF-8",
        "CI": "1",
        "NO_COLOR": "1",
        "FORCE_COLOR": "0",
        "PY_COLORS": "0",
        "TZ": "UTC",
    }


def test_gate_env_keeps_windows_system_variables() -> None:
    env = gate_env({"SystemRoot": "C:\\Windows", "Path": "C:\\bin"}, platform="win32")
    assert env["SystemRoot"] == "C:\\Windows"
    assert env["Path"] == "C:\\bin"
