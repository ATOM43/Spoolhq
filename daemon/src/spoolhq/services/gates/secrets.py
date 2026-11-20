"""The secret scan: no added line may carry something that looks like a credential.

Only added lines are scanned, and a hit is reported as its path, line and pattern name:
the value itself never goes into the result, so it can't reach a log, an event, the
retry prompt or the app. Every pattern is linear (possessive quantifiers, fixed
prefixes), since the agent controls the input. See ``docs/gates.md#secret-scan``.
"""

import math
import re
import time
from collections import Counter
from collections.abc import Iterable, Sequence

from spoolhq.services.gates.model import FileChange, GateName, GateResult, GateStatus
from spoolhq.services.gates.size import LOCKFILE_PATTERNS, is_exempt

SECRET_SCAN: GateName = "secret_scan"  # noqa: S105 (a gate name)
ALLOW_COMMENT = "spoolhq:allow-secret"
ENTROPY_MIN_CHARS = 32
ENTROPY_BITS = 4.5
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
    r"""(?<![\w.-])([\w.-]++)["']?\s*+(?::=|=|:)\s*+(["'])(?![/~.])[^\s"'{}<>$]{16,}+\2"""
)
_QUOTED = re.compile(rf"""(["'`])([^\s"'`]{{{ENTROPY_MIN_CHARS},}}+)\1""")


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
                return "high-entropy string"
    return None


def scan_secrets(changes: Iterable[FileChange], allow: Sequence[str]) -> GateResult:
    """Fail on each added line that looks like a secret, outside ``allow`` (globs) and
    lines carrying ``spoolhq:allow-secret``."""
    start = time.monotonic()
    hits: list[str] = []
    for change in changes:
        if is_exempt(change.path, allow):
            continue
        lockfile = is_exempt(change.path, LOCKFILE_PATTERNS)
        for line, text in change.added:
            if ALLOW_COMMENT in text:
                continue
            if (name := _hit(text, lockfile)) is not None:
                hits.append(f"Possible secret in {change.path}:{line} ({name})")
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
