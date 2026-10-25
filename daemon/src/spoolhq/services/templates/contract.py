"""``spoolhq-template.yaml``: what a template tells SpoolHQ about itself.

It sits at the template root (and is never copied into the generated project): the
template's name, a description for the planner and the ``install``, ``lint`` and
``test`` commands the gates run, with the same no-shell rule as ``project.yaml``.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, ValidationError
from ruamel.yaml.error import MarkedYAMLError, YAMLError

from spoolhq.services.gates import check_gate_command
from spoolhq.services.projects.errors import format_errors
from spoolhq.services.projects.model import check_slug
from spoolhq.services.projects.yaml_io import loader, to_plain

CONTRACT_FILE = "spoolhq-template.yaml"
MAX_DESCRIPTION = 2_000
REQUIRED_COMMANDS = ("install", "lint", "test")


class TemplateError(Exception):
    """A template can't be used: bad source, bad contract, unsafe features or a failed
    generation. The message says which template and why."""


def _check_command(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    return check_gate_command(value)


def _check_description(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be empty")
    if len(value) > MAX_DESCRIPTION:
        raise ValueError(f"must be at most {MAX_DESCRIPTION:,} characters, got {len(value):,}")
    return value


Command = Annotated[str, AfterValidator(_check_command)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class TemplateCommands(_Strict):
    install: Command
    lint: Command
    test: Command
    dev: Command | None = None

    def gates(self) -> dict[str, str]:
        """The commands the gates run, as ``project.yaml``'s ``commands``."""
        return {name: getattr(self, name) for name in REQUIRED_COMMANDS}


class TemplateContract(_Strict):
    name: Annotated[str, AfterValidator(check_slug)]
    description: Annotated[str, AfterValidator(_check_description)]
    commands: TemplateCommands


def _message(line: str, label: str) -> str:
    prefix = f"template {label!r}: {CONTRACT_FILE}"
    for command in REQUIRED_COMMANDS:
        if line == f"commands.{command}: field required":
            return (
                f"{prefix} has no {command!r} command; "
                "every template must declare install, lint and test"
            )
    return f"{prefix}: {line}"


def parse_contract(data: Any, label: str) -> TemplateContract:
    """Validate parsed YAML; TemplateError lists every problem, one line each."""
    if not isinstance(data, Mapping):
        raise TemplateError(f"template {label!r}: {CONTRACT_FILE}: expected a mapping")
    try:
        return TemplateContract.model_validate(to_plain(data))
    except ValidationError as exc:
        lines = format_errors(exc, TemplateContract, prefix=None)
        raise TemplateError("\n".join(_message(line, label) for line in lines)) from exc


def load_contract(root: Path, label: str) -> TemplateContract:
    """Read and validate ``<root>/spoolhq-template.yaml``."""
    path = root / CONTRACT_FILE
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise TemplateError(
            f"template {label!r}: no {CONTRACT_FILE} at the template root; "
            "every template must have one (docs/templates.md)"
        ) from None
    except (OSError, UnicodeDecodeError) as exc:
        raise TemplateError(f"template {label!r}: cannot read {CONTRACT_FILE}: {exc}") from exc
    try:
        data = loader().load(text)
    except MarkedYAMLError as exc:
        mark = exc.problem_mark or exc.context_mark
        where = f"line {mark.line + 1}, column {mark.column + 1}: " if mark else ""
        problem = exc.problem or exc.context or "invalid YAML"
        raise TemplateError(f"template {label!r}: {CONTRACT_FILE}: {where}{problem}") from exc
    except YAMLError as exc:
        raise TemplateError(f"template {label!r}: {CONTRACT_FILE}: invalid YAML: {exc}") from exc
    return parse_contract(data, label)
