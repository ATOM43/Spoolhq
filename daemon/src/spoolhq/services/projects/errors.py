"""Readable ``project.yaml`` errors: ``project.yaml: <dotted.path>: <message>``."""

import difflib
import types
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

FILE_NAME = "project.yaml"


class ProjectError(Exception):
    """A project could not be created, loaded or saved; the message says why."""


class ProjectValidationError(ProjectError):
    """``project.yaml`` (or the values given to ``spool init``) is invalid."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def dotted_path(loc: tuple[int | str, ...]) -> str:
    """``("merge_policy", "protected_paths", 0)`` -> ``merge_policy.protected_paths[0]``."""
    path = ""
    for part in loc:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else part
    return path


def _model_at(model: type[BaseModel], loc: tuple[int | str, ...]) -> type[BaseModel] | None:
    """The model class reached by following ``loc`` (field names only) from ``model``."""
    current: type[BaseModel] = model
    for part in loc:
        field = current.model_fields.get(str(part))
        if field is None:
            return None
        annotation: Any = field.annotation
        if get_origin(annotation) in (Union, types.UnionType):
            annotation = next((arg for arg in get_args(annotation) if arg is not type(None)), None)
        if not (isinstance(annotation, type) and issubclass(annotation, BaseModel)):
            return None
        current = annotation
    return current


def _number(value: Any) -> Any:
    """``0.0`` -> ``0``, so float bounds read like the YAML the user wrote."""
    return int(value) if isinstance(value, float) and value.is_integer() else value


def _message(error: ErrorDetails, model: type[BaseModel]) -> str:
    kind = error["type"]
    ctx = error.get("ctx", {})
    if kind == "missing":
        return "field required"
    if kind == "extra_forbidden":
        parent = _model_at(model, error["loc"][:-1])
        if parent is not None:
            close = difflib.get_close_matches(str(error["loc"][-1]), parent.model_fields, n=1)
            if close:
                return f"unknown key (did you mean {close[0]!r}?)"
        return "unknown key"
    if kind == "value_error":
        return str(ctx["error"])
    if kind == "greater_than":
        return f"must be greater than {_number(ctx['gt'])}"
    if kind == "greater_than_equal":
        return f"must be at least {_number(ctx['ge'])}"
    if kind == "less_than_equal":
        return f"must be at most {_number(ctx['le'])}"
    if kind == "literal_error":
        return f"must be one of {ctx['expected']}"
    message = error["msg"]
    return message[:1].lower() + message[1:]


def format_errors(
    exc: ValidationError, model: type[BaseModel], *, prefix: str | None = FILE_NAME
) -> list[str]:
    """One line per error, all of them, as ``<prefix>: <dotted.path>: <message>``."""
    lines = []
    for error in exc.errors():
        line = f"{dotted_path(error['loc'])}: {_message(error, model)}"
        lines.append(f"{prefix}: {line}" if prefix else line)
    return lines
