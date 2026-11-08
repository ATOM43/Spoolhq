"""An attempt's ``gates.json``, ``review.json`` and ``diff.patch`` as typed reports for
the Run tab. The files stay as the run loop writes them (the retry prompt, the PR body
and the policy read them); these functions only reshape them. All text is untrusted."""

import ast
import re
from dataclasses import dataclass
from typing import Any, Literal

from spoolhq.services.gates import first_failure, split_lines

GateState = Literal["passed", "failed", "timed_out", "skipped"]
FileStatus = Literal["added", "modified", "deleted", "renamed"]
PATCH_LINES = 2_000
"""A file's patch is cut after this many lines."""


@dataclass(frozen=True)
class GateReport:
    name: str
    command: str
    state: GateState
    duration_ms: int
    output: str
    """The trimmed output of a gate that didn't pass; empty for one that passed."""
    first_failure_line: int | None
    """Index of the first failure line in ``output``'s lines."""
    truncated: bool


@dataclass(frozen=True)
class GatesReport:
    passed: bool
    results: list[GateReport]
    stopped: str | None
    """The implementer stopped early (``max_turns``, …) and no gate ran."""


@dataclass(frozen=True)
class ReviewItem:
    text: str
    met: bool
    reason: str


@dataclass(frozen=True)
class ReviewReport:
    verdict: Literal["approve", "changes_requested", "needs_human"] | None
    """None when the reviewer didn't finish; ``stopped`` says why."""
    items: list[ReviewItem]
    """In the ticket's "Done when" order."""
    summary: str
    stopped: str | None


@dataclass(frozen=True)
class DiffFile:
    path: str
    old_path: str | None
    """The path before a rename."""
    status: FileStatus
    additions: int
    deletions: int
    binary: bool
    patch: str
    """The hunks, from the first ``@@`` line; empty for a binary or mode-only change."""
    truncated: bool


@dataclass(frozen=True)
class DiffReport:
    files: list[DiffFile]
    truncated: bool
    """Some file's patch was cut at ``PATCH_LINES``."""


def _state(status: str) -> GateState:
    if status in ("passed", "timed_out", "skipped"):
        return status  # type: ignore[return-value]
    return "failed"  # failed, and error: the program couldn't start


def gates_report(data: dict[str, Any]) -> GatesReport:
    """The report of a stored ``gates.json``."""
    if "stopped" in data:
        return GatesReport(passed=False, results=[], stopped=str(data["stopped"]))
    results = []
    for item in data.get("results", []):
        output = str(item.get("excerpt") or "")
        state = _state(str(item.get("status")))
        failure = first_failure(split_lines(output)) if state in ("failed", "timed_out") else None
        results.append(
            GateReport(
                name=str(item.get("name")),
                command=str(item.get("command") or ""),
                state=state,
                duration_ms=round(float(item.get("duration_s") or 0) * 1000),
                output=output,
                first_failure_line=failure,
                truncated=bool(item.get("output_truncated") or item.get("excerpt_trimmed")),
            )
        )
    return GatesReport(passed=bool(data.get("passed")), results=results, stopped=None)


def review_report(data: dict[str, Any]) -> ReviewReport:
    """The report of a stored ``review.json``."""
    if "stopped" in data:
        return ReviewReport(verdict=None, items=[], summary="", stopped=str(data["stopped"]))
    items = sorted(data.get("items", []), key=lambda item: int(item.get("index", 0)))
    verdict = data.get("verdict")
    return ReviewReport(
        verdict=verdict if verdict in ("approve", "changes_requested", "needs_human") else None,
        items=[
            ReviewItem(
                text=str(i.get("item")), met=bool(i.get("met")), reason=str(i.get("reason") or "")
            )
            for i in items
        ],
        summary=str(data.get("summary") or ""),
        stopped=None if verdict else str(data.get("run_outcome") or "error"),
    )


_QUOTED = r'"(?:[^"\\]|\\.)*"'
_HEADER_QUOTED = re.compile(f"({_QUOTED}) ({_QUOTED})")


def _unquote(name: str) -> str:
    """A path as git prints it: C-quoted (octal UTF-8 bytes) when it has odd characters,
    and with a tab after it when it has spaces."""
    name = name.removesuffix("\t")
    if len(name) >= 2 and name[0] == name[-1] == '"':
        try:
            value = ast.literal_eval("b" + name)
        except (ValueError, SyntaxError):
            return name[1:-1]
        return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else name
    return name


def _strip(path: str, prefix: str) -> str:
    path = _unquote(path)
    return path.removeprefix(prefix)


def _header_path(header: str) -> str:
    """The path in ``diff --git a/P b/P`` (both sides are the same unless renamed)."""
    quoted = _HEADER_QUOTED.fullmatch(header)
    if quoted:
        return _strip(quoted[2], "b/")
    half = (len(header) - 5) // 2  # "a/" + P + " b/" + P
    return header[2 : 2 + half] if half > 0 else header


def _file(chunk: str) -> DiffFile:
    lines = chunk.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    status: FileStatus = "modified"
    old = new = renamed_from = renamed_to = None
    binary = False
    start = len(lines)
    for index, line in enumerate(lines[1:], start=1):
        if line.startswith("@@"):
            start = index
            break
        if line.startswith("new file mode"):
            status = "added"
        elif line.startswith("deleted file mode"):
            status = "deleted"
        elif line.startswith("rename from "):
            renamed_from = _unquote(line.removeprefix("rename from "))
        elif line.startswith("rename to "):
            renamed_to = _unquote(line.removeprefix("rename to "))
        elif line.startswith("--- ") and line != "--- /dev/null":
            old = _strip(line[4:], "a/")
        elif line.startswith("+++ ") and line != "+++ /dev/null":
            new = _strip(line[4:], "b/")
        elif line.startswith(("Binary files ", "GIT binary patch")):
            binary = True
    if renamed_from is not None:
        status = "renamed"
    path = new or renamed_to or old or _header_path(lines[0])
    hunks = [] if binary else lines[start:]
    return DiffFile(
        path=path,
        old_path=renamed_from,
        status=status,
        additions=sum(1 for line in hunks if line.startswith("+")),
        deletions=sum(1 for line in hunks if line.startswith("-")),
        binary=binary,
        patch="\n".join(hunks[:PATCH_LINES]),
        truncated=len(hunks) > PATCH_LINES,
    )


def diff_report(text: str) -> DiffReport:
    """The files of a stored ``git diff`` (``diff.patch``), in diff order. Content lines
    start with a space, ``+``, ``-`` or ``\\``, so a line starting ``diff --git `` is
    always a file header; ``\\r`` at line ends is kept."""
    chunks = re.split(r"^diff --git ", text, flags=re.MULTILINE)[1:]
    files = [_file(chunk) for chunk in chunks]
    return DiffReport(files=files, truncated=any(f.truncated for f in files))
