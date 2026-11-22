"""Folders added to ``PATH`` so agent CLIs are found from a desktop launch.

An app started from a desktop menu or Finder gets a short ``PATH`` that may miss
``claude`` or ``codex``. The usual install folders and ``extra_path`` from
``config.toml`` are appended when they exist and are not already there; the user's
shell is never run to read its ``PATH``.
"""

import os
from collections.abc import Mapping, Sequence
from pathlib import Path

HOME_DIRS = (".local/bin", ".npm-global/bin", ".bun/bin", ".cargo/bin")
SYSTEM_DIRS = ("/opt/homebrew/bin", "/usr/local/bin")


def candidate_dirs(home: Path, platform: str, environ: Mapping[str, str]) -> list[Path]:
    """The usual install folders for this platform, existing or not."""
    if platform == "win32":
        appdata = environ.get("APPDATA")
        return [home / d for d in HOME_DIRS] + ([Path(appdata) / "npm"] if appdata else [])
    return [home / d for d in HOME_DIRS] + [Path(d) for d in SYSTEM_DIRS]


def extended_path(
    current: str,
    extra: Sequence[Path],
    *,
    home: Path,
    platform: str,
    environ: Mapping[str, str],
) -> str:
    """``current`` with each existing candidate folder, then each ``extra`` folder,
    appended once."""
    parts = [part for part in current.split(os.pathsep) if part]
    seen = {os.path.normcase(os.path.normpath(part)) for part in parts}
    for folder in [*candidate_dirs(home, platform, environ), *extra]:
        key = os.path.normcase(os.path.normpath(folder))
        if key not in seen and folder.is_dir():
            parts.append(str(folder))
            seen.add(key)
    return os.pathsep.join(parts)


def extend_process_path(extra: Sequence[Path], platform: str) -> None:
    """Set this process's ``PATH`` (inherited by agents) to :func:`extended_path`."""
    os.environ["PATH"] = extended_path(
        os.environ.get("PATH", ""), extra, home=Path.home(), platform=platform, environ=os.environ
    )
