"""Ticket files as text: split off the frontmatter, parse it, and update it in place.

A ticket file is a ``---`` line, YAML frontmatter, a closing ``---`` line and the body.
The body is kept as the exact original text and never re-rendered. The frontmatter is
parsed with ruamel.yaml in round-trip mode; when a ticket is saved, only the lines of
the keys whose value changed are rewritten, so comments, key order, quoting, spacing
and line endings of everything else survive byte for byte.
"""

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass
from io import StringIO
from typing import Any

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.error import MarkedYAMLError, YAMLError
from ruamel.yaml.reader import ReaderError
from ruamel.yaml.scalarstring import DoubleQuotedScalarString, SingleQuotedScalarString

from spoolhq.services.tickets.errors import TicketValidationError

DELIMITER = "---"
BOM = "﻿"

_LINE_RE = re.compile(r"[^\n]*\n|[^\n]+")


@dataclass
class TicketText:
    """A ticket file cut into its parts; joining them gives back the exact text."""

    head: str
    """The opening ``---`` line with its line ending (and a byte-order mark, if any)."""
    frontmatter: str
    close: str
    """The closing ``---`` line, with its line ending unless the file ends there."""
    body: str
    newline: str
    """``\\r\\n`` or ``\\n``, taken from the opening line; used for rewritten lines."""
    doc: Any
    """The parsed frontmatter (ruamel round-trip data)."""

    def join(self, frontmatter: str | None = None, body: str | None = None) -> str:
        fm = self.frontmatter if frontmatter is None else frontmatter
        return self.head + fm + self.close + (self.body if body is None else body)


def split_lines(text: str) -> list[str]:
    """Lines with their endings, split on ``\\n`` only (``\\r\\n`` stays on its line)."""
    return _LINE_RE.findall(text)


def _is_delimiter(line: str) -> bool:
    return line.rstrip() == DELIMITER


def split(text: str, source: str) -> TicketText:
    """Cut ``text`` into head, frontmatter, close and body, and parse the frontmatter."""
    lines = split_lines(text)
    if not lines or not _is_delimiter(lines[0].removeprefix(BOM)):
        raise TicketValidationError(
            [f"{source}: line 1: the file must start with a '---' line opening the frontmatter"]
        )
    end = next((i for i in range(1, len(lines)) if _is_delimiter(lines[i])), None)
    if end is None:
        raise TicketValidationError(
            [f"{source}: the frontmatter is not closed: add a '---' line after it"]
        )
    frontmatter = "".join(lines[1:end])
    return TicketText(
        head=lines[0],
        frontmatter=frontmatter,
        close=lines[end],
        body="".join(lines[end + 1 :]),
        newline="\r\n" if lines[0].endswith("\r\n") else "\n",
        doc=parse_yaml(frontmatter, source),
    )


def _loader() -> YAML:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    return yaml


def _dumper(*, sequence: int = 4, offset: int = 2) -> YAML:
    yaml = YAML(typ="rt")
    yaml.indent(mapping=2, sequence=sequence, offset=offset)
    yaml.width = 4096  # never re-wrap long values
    return yaml


def parse_yaml(frontmatter: str, source: str) -> Any:
    """Parse the frontmatter; syntax errors give the line and column in the file."""
    try:
        return _loader().load(frontmatter)
    except MarkedYAMLError as exc:
        mark = exc.problem_mark or exc.context_mark
        problem = exc.problem or exc.context or "invalid YAML"
        # +2: line numbers start at 1, and the opening '---' is line 1 of the file.
        where = f"line {mark.line + 2}, column {mark.column + 1}: " if mark else ""
        raise TicketValidationError([f"{source}: {where}{problem}"]) from exc
    except ReaderError as exc:
        before = frontmatter[: exc.position]
        line = before.count("\n") + 2
        column = len(before) - (before.rfind("\n") + 1) + 1
        code = exc.character if isinstance(exc.character, int) else ord(exc.character)
        character = f"#x{code:04x}"
        raise TicketValidationError(
            [f"{source}: line {line}, column {column}: unacceptable character {character}"]
        ) from exc
    except YAMLError as exc:
        first_line = str(exc).splitlines()[0] if str(exc) else "unknown error"
        raise TicketValidationError([f"{source}: invalid YAML: {first_line}"]) from exc


def to_plain(value: Any) -> Any:
    """ruamel's containers and scalar subclasses as plain Python values, for Pydantic."""
    if isinstance(value, Mapping):
        return {str(key): to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    for kind in (bool, int, float, str):
        if isinstance(value, kind):
            return kind(value)
    return value


# Updating the frontmatter -------------------------------------------------------------


def update_frontmatter(text: TicketText, changes: Mapping[str, Any]) -> str:
    """The frontmatter with ``changes`` applied, rewriting only the changed keys' lines.

    Keys not yet in the file are appended. If the result would not read back as the
    intended values (for example a frontmatter written as one flow mapping), the whole
    frontmatter is re-rendered by ruamel instead, which still keeps comments.
    """
    if not changes:
        return text.frontmatter
    expected = {**to_plain(text.doc), **to_plain(dict(changes))}
    try:
        spliced = _splice(text, changes)
        if to_plain(_loader().load(spliced)) == expected:
            return spliced
    except (YAMLError, ValueError):
        pass
    return _redump(text.doc, changes, text.newline)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _is_gap(line: str, key_col: int) -> bool:
    """A blank line, or a comment no deeper than the key: kept between entries."""
    stripped = line.strip()
    return not stripped or (stripped.startswith("#") and _indent(line) <= key_col)


def _splice(text: TicketText, changes: Mapping[str, Any]) -> str:
    doc = text.doc
    if not isinstance(doc, CommentedMap) or doc.fa.flow_style():
        raise ValueError("frontmatter is not a block mapping")
    lines = split_lines(text.frontmatter)
    keys = list(doc)
    starts = [doc.lc.key(key)[0] for key in keys]

    spans: dict[str, tuple[int, int]] = {}
    for index, key in enumerate(keys):
        start = starts[index]
        end = starts[index + 1] if index + 1 < len(keys) else len(lines)
        while end > start + 1 and _is_gap(lines[end - 1], doc.lc.key(key)[1]):
            end -= 1
        spans[key] = (start, end)

    # Replace from the bottom up so earlier line numbers stay valid.
    present = sorted((key for key in changes if key in doc), key=lambda k: -spans[k][0])
    for key in present:
        start, end = spans[key]
        lines[start:end] = _render_entry(text, key, changes[key], lines[start:end])
    added = [key for key in changes if key not in doc]
    # The frontmatter always ends with a line break: the closing '---' is on its own line.
    for key in added:
        lines.extend(_render_entry(text, key, changes[key], []))
    return "".join(lines)


def _render_entry(text: TicketText, key: str, value: Any, old_lines: list[str]) -> list[str]:
    """``key: value`` as lines in the file's style, keeping the key line's comment."""
    doc = text.doc
    old = doc.get(key)
    col = doc.lc.key(key)[1] if key in doc else 0
    comment = ""
    sequence, offset = 4, 2
    if old_lines:
        value_line, value_col = doc.lc.value(key)
        start = value_col if value_line == doc.lc.key(key)[0] else col
        comment = _inline_comment(old_lines[0], start)
        sequence, offset = _block_indent(old_lines[1:], col)

    if value is None:
        rendered = [f"{key}: null"]
    else:
        stream = StringIO()
        _dumper(sequence=sequence, offset=offset).dump({key: _node(value, old)}, stream)
        rendered = [line.rstrip("\n") for line in split_lines(stream.getvalue())]
    rendered[0] += comment
    return [" " * col + line + text.newline for line in rendered]


def _block_indent(item_lines: list[str], key_col: int) -> tuple[int, int]:
    """ruamel's (sequence, offset) indents that reproduce the old block list's layout."""
    for line in item_lines:
        stripped = line.lstrip(" ")
        if stripped.startswith("- "):
            dash = _indent(line) - key_col
            gap = len(stripped[1:]) - len(stripped[1:].lstrip(" "))
            if dash >= 0:
                return dash + 1 + gap, dash
    return 4, 2


def _inline_comment(line: str, start: int) -> str:
    """The ``  # comment`` at the end of ``line`` (with the spaces before it), or ``""``.

    Scans from ``start`` (where the value begins), skipping ``#`` inside quoted scalars.
    """
    content = line.rstrip("\r\n")
    quote: str | None = None
    previous: str | None = None  # the last non-blank character outside quotes
    index = start
    while index < len(content):
        char = content[index]
        if quote == "'":
            if char == "'":
                if content[index + 1 : index + 2] == "'":
                    index += 1
                else:
                    quote = None
        elif quote == '"':
            if char == "\\":
                index += 1
            elif char == '"':
                quote = None
        elif char in "'\"" and previous in (None, ":", "[", "{", ","):
            quote = char
        elif char == "#" and index > 0 and content[index - 1] in " \t":
            begin = index
            while begin > start and content[begin - 1] in " \t":
                begin -= 1
            return content[begin:]
        if quote is None and char not in " \t":
            previous = char
        index += 1
    return ""


def _styled(value: Any, like: Any) -> Any:
    """``value`` with the quote style of ``like`` (the value it replaces), if it had one."""
    if isinstance(value, str) and isinstance(
        like, SingleQuotedScalarString | DoubleQuotedScalarString
    ):
        return type(like)(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _node(value: Any, old: Any) -> Any:
    if isinstance(value, list):
        like = old[0] if isinstance(old, list) and old else None
        seq = CommentedSeq(_styled(item, like) for item in value)
        # An empty list can only have been written as `[]`, so it stays in flow style.
        if not value or not isinstance(old, CommentedSeq) or not old or old.fa.flow_style():
            seq.fa.set_flow_style()
        return seq
    return _styled(value, old)


def _redump(doc: Any, changes: Mapping[str, Any], newline: str) -> str:
    """The whole frontmatter re-rendered by ruamel, with ``changes`` applied."""
    doc = copy.deepcopy(doc) if isinstance(doc, CommentedMap) else CommentedMap()
    for key, value in changes.items():
        doc[key] = _node(value, doc.get(key))
    stream = StringIO()
    _dumper().dump(doc, stream)
    return stream.getvalue().replace("\n", newline)
