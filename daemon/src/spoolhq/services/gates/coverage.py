"""The coverage total: read from the report the test command writes, kept for main.

A report is Cobertura XML (``<coverage line-rate="0.912">``) or a JSON summary
(coverage.py's ``totals.percent_covered`` or Istanbul's ``total.lines.pct``). The XML
is read with a regex on its root tag, never a parser, since the agent wrote the code
that wrote it. Main's total lives in ``<workspace>/coverage.json``, written at each
merge (see ``docs/gates.md#coverage``).
"""

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

STORE_FILE = "coverage.json"
_COBERTURA = re.compile(r"<coverage\b[^>]*?\bline-rate=\"([0-9.]+)\"")


def _number(data: Any, *keys: str) -> float | None:
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return float(data) if isinstance(data, int | float) and not isinstance(data, bool) else None


def read_total(worktree: Path, report: str) -> float | None:
    """The total percentage in ``report`` (relative to ``worktree``), or ``None`` when it
    is missing, outside the worktree or unreadable."""
    path = worktree / report
    try:
        if not path.resolve().is_relative_to(worktree.resolve()) or not path.is_file():
            return None
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    total: float | None
    if text.lstrip().startswith("{"):
        try:
            data = json.loads(text)
        except ValueError:
            return None
        total = _number(data, "totals", "percent_covered")
        if total is None:
            total = _number(data, "total", "lines", "pct")
    else:
        match = _COBERTURA.search(text[:10_000])
        total = float(match.group(1)) * 100 if match else None
    return round(total, 2) if total is not None and 0 <= total <= 100 else None


def stored_total(workspace: Path) -> float | None:
    """Main's total at the last merge that had one, or ``None``."""
    try:
        data = json.loads((workspace / STORE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _number(data, "total")


def store_total(workspace: Path, total: float, ticket_id: str) -> None:
    """Write main's total atomically."""
    content = json.dumps({"total": total, "ticket": ticket_id}) + "\n"
    fd, temp = tempfile.mkstemp(prefix=f".{STORE_FILE}.", suffix=".tmp", dir=workspace)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp, workspace / STORE_FILE)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise
