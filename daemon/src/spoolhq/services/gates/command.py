"""Gate commands: split without a shell, resolve the program, scrub the environment."""

import fnmatch
import shlex
import shutil
from collections.abc import Mapping

from spoolhq.core.agent_policy import allowed_env

SHELL_SYNTAX = ("&&", "||", "|", ";", ">", "<", "`", "$(")
SHELL_SYNTAX_ERROR = "shell syntax isn't supported; put it in a justfile recipe"
# Never passed to a gate, even if the allowlist ever grows to match one.
SECRET_PATTERNS = ("ANTHROPIC_API_KEY", "*_TOKEN", "*_KEY", "*_SECRET", "*_PASSWORD")
GATE_ENV_SET = {
    "CI": "1",  # no watch modes or prompts
    "NO_COLOR": "1",
    "FORCE_COLOR": "0",
    "PY_COLORS": "0",
    "TZ": "UTC",
}


def split_command(command: str) -> list[str]:
    """``command`` as an argument list; ``ValueError`` for shell syntax or bad quoting."""
    if any(token in command for token in SHELL_SYNTAX):
        raise ValueError(SHELL_SYNTAX_ERROR)
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"can't be split into arguments: {exc}") from exc
    if not argv:
        raise ValueError("must not be empty")
    return argv


def check_gate_command(command: str) -> str:
    """Validator for ``project.yaml``'s ``commands.*``."""
    split_command(command)
    return command


def resolve_program(program: str, env: Mapping[str, str]) -> str | None:
    """The program's path, looked up on the scrubbed ``PATH``, or ``None``."""
    path = next((value for name, value in env.items() if name.upper() == "PATH"), None)
    return shutil.which(program, path=path)


def gate_env(parent: Mapping[str, str], *, platform: str) -> dict[str, str]:
    """The agent's environment allowlist, minus anything secret-looking, plus GATE_ENV_SET."""
    env = {
        name: value
        for name, value in allowed_env(parent, platform=platform).items()
        if not any(fnmatch.fnmatchcase(name.upper(), pattern) for pattern in SECRET_PATTERNS)
    }
    env.update(GATE_ENV_SET)
    return env
