"""The project's Graphify cache, outside the repository, and refreshing the map from it.

``<workspace>/.spoolhq/codegraph/`` holds ``current.json`` (``{"build": "b-…",
"version": "0.9.92"}``) and the build it names, a ``graphify-out/`` folder with
Graphify's content-hash cache, ``graph.json`` and ``GRAPH_REPORT.md``. A refresh copies
the current build to a ``tmp-…`` folder, runs Graphify there with ``--out`` (so it writes
nothing into the checkout), renames the folder to a new ``b-…`` build and only then
replaces ``current.json`` (``os.replace``, atomic). A crash at any point leaves the
previous build and pointer as they were; leftover folders are removed next time.
"""

import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from spoolhq.core.daemon_lock import LockHeld, acquire_lock
from spoolhq.services.codegraph import tool
from spoolhq.services.codegraph.report import summary
from spoolhq.services.codegraph.tool import Graphify, GraphifyError

logger = logging.getLogger(__name__)

CACHE_DIR = ".spoolhq/codegraph"
POINTER = "current.json"
LOCK = "lock"
OUT = "graphify-out"
REPORT = "GRAPH_REPORT.md"
_BUILD, _TMP = "b-", "tmp-"


@dataclass(frozen=True)
class CodeMap:
    text: str
    """The report's summary (see ``report.summary``); untrusted, from the repository."""
    kind: Literal["full", "update"]
    seconds: float


def cache_dir(workspace: Path) -> Path:
    return workspace / CACHE_DIR


def refresh(source: Path, workspace: Path) -> CodeMap | None:
    """Build or update the code map of ``source`` with the project's cache; None, after
    one log line, when Graphify is missing, busy or fails twice."""
    graphify = tool.probe()
    if graphify is None:
        logger.info("no code map: graphify is not on PATH or its version can't be read")
        return None
    if not graphify.tested:
        logger.warning(
            "graphify %s is untested; SpoolHQ is tested with %s",
            graphify.version,
            tool.TESTED_VERSION,
        )
    folder = cache_dir(workspace)
    try:
        lock = acquire_lock(folder / LOCK)
    except LockHeld:
        logger.info("no code map: the code graph cache is in use by another run")
        return None
    with lock:
        return _refresh(graphify, source, folder)


def _refresh(graphify: Graphify, source: Path, folder: Path) -> CodeMap | None:
    start = time.monotonic()
    current = _current(folder, graphify.version)
    _remove_unused(folder, keep=current)
    kind: Literal["full", "update"] = "update" if current else "full"
    work = folder / f"{_TMP}{uuid.uuid4().hex}"
    if current:
        shutil.copytree(folder / current, work)
    try:
        _build(graphify, source, work, full=not current)
    except (GraphifyError, OSError) as exc:
        shutil.rmtree(work, ignore_errors=True)
        if not current:
            logger.warning("no code map: %s", exc)
            return None
        logger.warning("code graph update failed, rebuilding from scratch: %s", exc)
        _drop(folder)
        return _refresh(graphify, source, folder)
    text = (work / OUT / REPORT).read_text(encoding="utf-8", errors="replace")
    try:
        _save(folder, work, graphify.version)
    except OSError as exc:
        logger.warning("cannot save the code graph cache: %s", exc)
    built = CodeMap(summary(text), kind, time.monotonic() - start)
    logger.info("code map: %s build in %.1f s, %d characters", kind, built.seconds, len(built.text))
    return built


def _build(graphify: Graphify, source: Path, work: Path, *, full: bool) -> None:
    """``extract`` (incremental against ``work``'s cache unless ``full``), then
    ``cluster-only`` for the report; the whole build within ``TIMEOUT_S``."""
    work.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + tool.TIMEOUT_S
    extract = ["extract", str(source), "--code-only", "--out", str(work)]
    extract += ["--force"] if full else []  # a full build skips Graphify's own cache
    tool.run(graphify.command, extract, cwd=work, timeout=tool.TIMEOUT_S)
    cluster = ["cluster-only", str(work), "--no-label", "--no-viz"]
    tool.run(graphify.command, cluster, cwd=work, timeout=deadline - time.monotonic())
    if not (work / OUT / REPORT).is_file():
        raise GraphifyError(f"graphify wrote no {OUT}/{REPORT}")


def _current(folder: Path, version: str) -> str | None:
    """The current build's folder name; None without one, or for another version's cache."""
    try:
        pointer = json.loads((folder / POINTER).read_text(encoding="utf-8"))
        build, built_by = str(pointer["build"]), str(pointer["version"])
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if not build.startswith(_BUILD) or not (folder / build / OUT).is_dir():
        return None
    if built_by != version:
        logger.info("code graph cache is from graphify %s; rebuilding with %s", built_by, version)
        _drop(folder)
        return None
    return build


def _save(folder: Path, work: Path, version: str) -> None:
    build = f"{_BUILD}{uuid.uuid4().hex}"
    work.rename(folder / build)
    staged = folder / f"{POINTER}.{uuid.uuid4().hex}.tmp"
    staged.write_text(json.dumps({"build": build, "version": version}), encoding="utf-8")
    os.replace(staged, folder / POINTER)
    _remove_unused(folder, keep=build)


def _drop(folder: Path) -> None:
    """Delete the cache: the pointer, then every build."""
    (folder / POINTER).unlink(missing_ok=True)
    _remove_unused(folder, keep=None)


def _remove_unused(folder: Path, keep: str | None) -> None:
    for path in folder.iterdir() if folder.is_dir() else ():
        if path.name != keep and path.name.startswith((_BUILD, _TMP, POINTER + ".")):
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
