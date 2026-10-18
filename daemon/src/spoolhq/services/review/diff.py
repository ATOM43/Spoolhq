"""Fitting a diff into the reviewer's prompt: pure.

Over the cap, every file's header and the list of changed files are kept, and whole
files follow in diff order while they fit; the reviewer reads the rest with ``Read``.
"""

import re

DIFF_MAX_CHARS = 150_000

_FILE_START_RE = re.compile(r"^diff --git ", re.MULTILINE)
_HUNK_RE = re.compile(r"^@@", re.MULTILINE)
_PATH_RE = re.compile(r"diff --git a/.* b/(.*)")


def _split_files(diff: str) -> tuple[str, list[str]]:
    """The text before the first ``diff --git`` line, and one chunk per file."""
    starts = [match.start() for match in _FILE_START_RE.finditer(diff)]
    if not starts:
        return diff, []
    bounds = [*starts, len(diff)]
    return diff[: starts[0]], [diff[a:b] for a, b in zip(bounds, bounds[1:], strict=False)]


def _header(chunk: str) -> str:
    """The file's lines before its first hunk (all of it for a binary or rename-only file)."""
    hunk = _HUNK_RE.search(chunk)
    return chunk if hunk is None else chunk[: hunk.start()]


def _path(chunk: str) -> str:
    match = _PATH_RE.match(chunk.split("\n", 1)[0])
    return match[1] if match else chunk.split("\n", 1)[0]


def trim_diff(diff: str, limit: int = DIFF_MAX_CHARS) -> tuple[str, bool]:
    """``diff`` if it fits in ``limit`` characters, else its trimmed form; and whether it was."""
    if len(diff) <= limit:
        return diff, False
    preamble, files = _split_files(diff)
    paths = [_path(chunk) for chunk in files]
    listing = f"Changed files ({len(files)}):\n" + "".join(f"- {p}\n" for p in paths) + "\n"
    headers = [_header(chunk) for chunk in files]

    def note(shown: int) -> str:
        return (
            f"\n[diff trimmed: {shown} of {len(files)} files shown in full; "
            "read the others with the Read tool]\n"
        )

    # The note at its longest, so upgrading files can't push the total over.
    room = limit - len(preamble) - len(listing) - sum(map(len, headers)) - len(note(len(files)))
    shown = 0
    for chunk, header in zip(files, headers, strict=True):
        extra = len(chunk) - len(header)
        if extra > room:
            break
        room -= extra
        shown += 1
    text = preamble + listing + "".join(files[:shown]) + "".join(headers[shown:]) + note(shown)
    if len(text) > limit:
        # shortcut: with thousands of files even the headers don't fit; cut at a line.
        text = text[: text.rfind("\n", 0, limit - len(note(shown))) + 1] + note(shown)
    return text, True
