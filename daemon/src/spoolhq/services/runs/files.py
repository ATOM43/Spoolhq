"""The files of an attempt, in its folder ``<workspace>/runs/<ticket>/<NNN>/``.

Only a fixed set of names can be written, so agent output never chooses a path. The
folder comes from the attempt's database row and must resolve inside
``<workspace>/runs/``.
"""

import contextlib
import json
import os
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Any

from spoolhq.services.runs.log import RUNS_DIR
from spoolhq.services.runs.model import Attempt


class ArtifactName(StrEnum):
    TRANSCRIPT = "transcript.jsonl"
    GATES = "gates.json"
    DIFF = "diff.patch"
    REVIEW = "review.json"


ARTIFACT_NAMES = frozenset(name.value for name in ArtifactName)


def _artifact_name(name: str) -> str:
    if name not in ARTIFACT_NAMES:
        allowed = ", ".join(sorted(ARTIFACT_NAMES))
        raise ValueError(f"invalid attempt file name {name!r}; allowed: {allowed}")
    return str(name)


def attempt_dir(workspace: Path, attempt: Attempt) -> Path:
    """The attempt's folder, from its row's ``dir``; ValueError if that leaves
    ``<workspace>/runs/`` (an absolute path, ``..`` or a symlink pointing out)."""
    runs_root = (workspace / RUNS_DIR).resolve()
    relative = Path(attempt.dir)
    folder = (workspace / relative).resolve()
    if relative.is_absolute() or folder == runs_root or not folder.is_relative_to(runs_root):
        raise ValueError(
            f"attempt {attempt.id}: folder {attempt.dir!r} is outside {RUNS_DIR}/ of the workspace"
        )
    return folder


def write_artifact(attempt: Attempt, name: str, data: str | bytes) -> Path:
    """Write one of the allowed files atomically: a temp file in the same folder, then
    ``os.replace``. Text is written as UTF-8 without newline translation."""
    file_name = _artifact_name(name)
    folder = attempt_dir(attempt.workspace, attempt)
    target = folder / file_name
    content = data.encode("utf-8") if isinstance(data, str) else data
    fd, temp_name = tempfile.mkstemp(prefix=f".{file_name}.", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, target)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise
    return target


def append_transcript(attempt: Attempt, record: dict[str, Any]) -> Path:
    """Append one JSON line to ``transcript.jsonl``, flushed and fsynced."""
    if not isinstance(record, dict):
        raise ValueError(f"transcript record must be a dict, got {type(record).__name__}")
    try:
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"transcript record is not JSON-serialisable: {exc}") from exc
    target = attempt_dir(attempt.workspace, attempt) / ArtifactName.TRANSCRIPT.value
    with target.open("ab") as file:
        file.write(line.encode("utf-8") + b"\n")
        file.flush()
        os.fsync(file.fileno())
    return target


def attempt_files(workspace: Path, attempt: Attempt) -> dict[str, Path]:
    """The allowed files the attempt has, by name, resolved from its row's ``dir``."""
    folder = attempt_dir(workspace, attempt)
    return {
        name.value: folder / name.value for name in ArtifactName if (folder / name.value).is_file()
    }
