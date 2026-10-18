"""Fail when a source file is over the line limit (tests are exempt).

Run by `just lint`. A file that must stay longer goes in ALLOWED with the reason.
Standard library only, so it runs before any dependency is installed.
"""

import sys
from pathlib import Path

LIMIT = 500
ROOT = Path(__file__).resolve().parent.parent
SOURCES = (
    (ROOT / "daemon" / "src" / "spoolhq", ("*.py",)),
    (ROOT / "desktop" / "src", ("*.ts", "*.tsx")),
)
# Repo-relative path -> why it may be longer than LIMIT.
ALLOWED: dict[str, str] = {}


def is_test(path: Path) -> bool:
    return ".test." in path.name or ".spec." in path.name


def oversized() -> list[tuple[str, int]]:
    found = []
    for folder, patterns in SOURCES:
        for pattern in patterns:
            for path in sorted(folder.rglob(pattern)):
                if is_test(path):
                    continue
                name = path.relative_to(ROOT).as_posix()
                lines = len(path.read_text(encoding="utf-8").splitlines())
                if lines > LIMIT and name not in ALLOWED:
                    found.append((name, lines))
    return found


def main() -> int:
    found = oversized()
    for name, lines in found:
        print(f"{name}: {lines} lines, over the {LIMIT}-line limit; split it", file=sys.stderr)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
