"""The secret scan: no added line may carry something that looks like a credential.

Only added lines are scanned, and a hit is reported as its path, line and pattern name:
the value itself never goes into the result, so it can't reach a log, an event, the
retry prompt or the app. Every pattern is linear (possessive quantifiers, fixed
prefixes), since the agent controls the input. See ``docs/gates.md#secret-scan``.

``redact`` replaces what the named patterns match with ``[redacted: <name>]`` in text
SpoolHQ stores (agent events, transcripts, ``diff.patch``, gate logs); a high-entropy
value is redacted only after the scan finds it (``high_entropy_values``).
"""

import math
import re
import time
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path
from typing import Any

from spoolhq.services.gates.model import FileChange, GateName, GateResult, GateStatus
from spoolhq.services.gates.size import LOCKFILE_PATTERNS, is_exempt

SECRET_SCAN: GateName = "secret_scan"  # noqa: S105 (a gate name)
ALLOW_COMMENT = "spoolhq:allow-secret"
ENTROPY_MIN_CHARS = 32
ENTROPY_BITS = 4.5
HIGH_ENTROPY = "high-entropy string"
LISTED_HITS = 50
SECRET_NAMES = ("key", "secret", "token", "password")
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private key", re.compile(r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:gh[po]_[A-Za-z0-9]{20,}+|github_pat_[A-Za-z0-9_]{20,}+)")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}+")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}+")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}+")),
)
# name = "value": the name is checked in code; a value that looks like a path or a
# template (``/``, ``~``, ``.`` first, or ``$ { } < >`` in it) isn't a literal secret.
_ASSIGNMENT = re.compile(
    r"""(?<![\w.-])([\w.-]++)["']?\s*+(?::=|=|:)\s*+(["'])(?![/~.])([^\s"'{}<>$]{16,}+)\2"""
)
_QUOTED = re.compile(rf"""(["'`])([^\s"'`]{{{ENTROPY_MIN_CHARS},}}+)\1""")
# Redaction takes the key's body too, keeping line breaks (and a diff's ``+``) so a
# stored diff still parses; the header alone is no secret.
_KEY_BLOCK = re.compile(r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY-----[A-Za-z0-9+/=\s]*+")
_KEY_BODY = re.compile(r"[A-Za-z0-9/=][A-Za-z0-9+/=]{15,}+")
# Redaction also runs on JSON text (a tool call's input), where ``\nsk-…`` has no ``\b``.
_REDACT = tuple(
    (name, re.compile(pattern.pattern.replace(r"\b", r"(?:(?<=\\[nrt])|\b)", 1)))
    for name, pattern in PATTERNS[1:]
)


def marker(name: str) -> str:
    return f"[redacted: {name}]"


def entropy(text: str) -> float:
    """Shannon entropy in bits per character."""
    counts, size = Counter(text), len(text)
    return -sum(count / size * math.log2(count / size) for count in counts.values())


def _hit(text: str, lockfile: bool) -> str | None:
    """The name of the first pattern ``text`` matches, or ``None``."""
    for name, pattern in PATTERNS:
        if pattern.search(text):
            return name
    for match in _ASSIGNMENT.finditer(text):
        if any(word in match.group(1).lower() for word in SECRET_NAMES):
            return "secret assignment"
    if not lockfile:
        for match in _QUOTED.finditer(text):
            if entropy(match.group(2)) > ENTROPY_BITS:
                return HIGH_ENTROPY
    return None


def _assignment(match: re.Match[str]) -> str:
    if not any(word in match.group(1).lower() for word in SECRET_NAMES):
        return match.group(0)
    start, end = match.start(3) - match.start(), match.end(3) - match.start()
    whole = match.group(0)
    return whole[:start] + marker("secret assignment") + whole[end:]


def redact(text: str) -> str:
    """``text`` with every named pattern's match replaced by ``[redacted: <name>]``."""
    text = _KEY_BLOCK.sub(lambda m: _KEY_BODY.sub(marker("private key"), m.group(0)), text)
    for name, pattern in _REDACT:
        text = pattern.sub(marker(name), text)
    return _ASSIGNMENT.sub(_assignment, text)


def redact_data(value: Any) -> Any:
    """``value`` with ``redact`` applied to every string in it (dict keys too)."""
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, dict):
        return {redact_data(key): redact_data(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [redact_data(item) for item in value]
    return value


def redact_file(path: Path) -> None:
    """Redact a stored text file in place (bytes that aren't UTF-8 are kept)."""
    text = path.read_bytes().decode("utf-8", errors="surrogateescape")
    if (clean := redact(text)) != text:
        path.write_bytes(clean.encode("utf-8", errors="surrogateescape"))


def _scanned(
    changes: Iterable[FileChange], allow: Sequence[str]
) -> Iterator[tuple[str, int, str, str]]:
    """Each flagged added line as (path, line, text, pattern name)."""
    for change in changes:
        if is_exempt(change.path, allow):
            continue
        lockfile = is_exempt(change.path, LOCKFILE_PATTERNS)
        for line, text in change.added:
            if ALLOW_COMMENT in text:
                continue
            if (name := _hit(text, lockfile)) is not None:
                yield change.path, line, text, name


def high_entropy_values(changes: Iterable[FileChange], allow: Sequence[str]) -> set[str]:
    """The values on lines that only the high-entropy rule flags, to redact after a hit."""
    return {
        match.group(2)
        for _, _, text, name in _scanned(changes, allow)
        if name == HIGH_ENTROPY
        for match in _QUOTED.finditer(text)
        if entropy(match.group(2)) > ENTROPY_BITS
    }


def scan_secrets(changes: Iterable[FileChange], allow: Sequence[str]) -> GateResult:
    """Fail on each added line that looks like a secret, outside ``allow`` (globs) and
    lines carrying ``spoolhq:allow-secret``."""
    start = time.monotonic()
    hits = [
        f"Possible secret in {path}:{line} ({name})"
        for path, line, _, name in _scanned(changes, allow)
    ]
    listed = hits[:LISTED_HITS]
    if len(hits) > LISTED_HITS:
        listed.append(f"… and {len(hits) - LISTED_HITS} more")
    return GateResult(
        name=SECRET_SCAN,
        command="secret scan",
        status=GateStatus.FAILED if hits else GateStatus.PASSED,
        exit_code=None,
        duration_s=time.monotonic() - start,
        excerpt="\n".join(listed),
        failing_tests=(),
        output_lines=len(listed),
        output_truncated=False,
        log_path=None,
    )
