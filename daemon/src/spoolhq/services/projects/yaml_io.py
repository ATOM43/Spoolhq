"""Reading and writing ``project.yaml`` with ruamel.yaml in round-trip mode.

Round-trip mode keeps the user's comments, key order and quoting when a file is
loaded, changed and saved. Its loader is safe: tags such as ``!!python/object`` are
kept as plain tagged data and never construct Python objects.
"""

import os
import tempfile
from collections.abc import Mapping
from io import StringIO
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import MarkedYAMLError, YAMLError

from spoolhq.services.projects.errors import FILE_NAME, ProjectError


def _yaml() -> YAML:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096  # never re-wrap long values
    return yaml


def parse(text: str) -> Any:
    """Parse YAML text, reporting syntax errors with their line and column."""
    try:
        return _yaml().load(text)
    except MarkedYAMLError as exc:
        mark = exc.problem_mark or exc.context_mark
        problem = exc.problem or exc.context or "invalid YAML"
        where = f"line {mark.line + 1}, column {mark.column + 1}: " if mark else ""
        raise ProjectError(f"{FILE_NAME}: {where}{problem}") from exc
    except YAMLError as exc:
        raise ProjectError(f"{FILE_NAME}: invalid YAML: {exc}") from exc


def read(path: Path) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProjectError(f"{FILE_NAME}: not found at {path}") from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise ProjectError(f"{FILE_NAME}: cannot read {path}: {exc}") from exc
    return parse(text)


def to_plain(value: Any) -> Any:
    """ruamel's comment-carrying containers as plain dicts and lists, for Pydantic."""
    if isinstance(value, Mapping):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def to_node(value: Any) -> Any:
    """Plain data as ruamel containers; lists of scalars are written in flow style."""
    if isinstance(value, Mapping):
        node = CommentedMap()
        for key, item in value.items():
            node[key] = to_node(item)
        return node
    if isinstance(value, list):
        seq = CommentedSeq(to_node(item) for item in value)
        if not any(isinstance(item, Mapping | list) for item in value):
            seq.fa.set_flow_style()
        return seq
    return value


def merge(doc: CommentedMap, data: Mapping[str, Any]) -> None:
    """Make ``doc`` hold ``data``, touching only keys whose value changed.

    Unchanged keys keep their comments and formatting; keys missing from ``data`` are
    removed.
    """
    for key in [key for key in doc if key not in data]:
        del doc[key]
    for key, value in data.items():
        current = doc.get(key)
        if isinstance(value, Mapping) and isinstance(current, CommentedMap):
            merge(current, value)
        elif key not in doc or current != value:
            doc[key] = to_node(value)


def dump(doc: Any) -> str:
    stream = StringIO()
    _yaml().dump(doc, stream)
    return stream.getvalue()


def write_atomic(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` via a temp file in the same folder and a rename."""
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        if path.exists():
            # mkstemp creates the file 0600; keep the mode the user's file had.
            tmp.chmod(path.stat().st_mode & 0o777)
        tmp.replace(path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
