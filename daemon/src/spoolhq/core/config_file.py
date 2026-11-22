"""Writing one value into ``config.toml`` without disturbing the rest of the file."""

import os
import tomllib
from pathlib import Path

from spoolhq.core.config import ConfigError


def set_bool(path: Path, table: str, key: str, value: bool) -> None:
    """Set ``[table] key = value`` in the TOML file at ``path``, creating either if missing.

    Other lines, comments included, are kept as they are. The result is parsed before it
    is written; a file this can't edit safely (the key set another way, invalid TOML) is
    left untouched and raises ``ConfigError``.
    """
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    entry = f"{key} = {'true' if value else 'false'}\n"
    start = next((i for i, line in enumerate(lines) if line.strip() == f"[{table}]"), None)
    if start is None:
        lines += ["\n" if lines else "", f"[{table}]\n", entry]
    else:
        end = next(
            (i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("[")),
            len(lines),
        )
        found = next(
            (i for i in range(start + 1, end) if lines[i].split("=")[0].strip() == key), None
        )
        if found is None:
            lines.insert(start + 1, entry)
        else:
            lines[found] = entry
    updated = "".join(lines)
    try:
        written = tomllib.loads(updated)[table][key]
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ConfigError(f"cannot set {table}.{key} in {path}: {exc}") from exc
    if written is not value:
        raise ConfigError(f"cannot set {table}.{key} in {path}")
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(updated, encoding="utf-8", newline="\n")
    os.replace(temp, path)
