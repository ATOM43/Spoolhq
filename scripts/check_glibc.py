"""Fail when a Linux binary needs a newer glibc than the oldest supported system.

    check_glibc.py <max, e.g. 2.35> <file or folder>...

Each ELF file under the paths is read for the `GLIBC_x.y` versions it names; inside a
PyInstaller one-file binary (the sidecar) the bundled libraries are read too, which needs
PyInstaller (run with the daemon's `build` group). Prints the highest version found and
exits 1 if it is above `max` (docs/packaging.md).
"""

import re
import sys
from collections.abc import Iterator
from pathlib import Path

ELF = b"\x7fELF"
PYINSTALLER_COOKIE = b"MEI\x0c\x0b\x0a\x0b\x0e"
# shortcut: a byte scan, not a parse of .gnu.version_r, so a library that also defines
# GLIBC_ versions (libc itself) counts as needing them; fine while none is bundled.
GLIBC = re.compile(rb"GLIBC_(\d+)\.(\d+)(?:\.(\d+))?\b")

Version = tuple[int, ...]


def parse(text: str) -> Version:
    return tuple(int(part) for part in text.split("."))


def show(version: Version) -> str:
    return ".".join(str(part) for part in version)


def highest(data: bytes) -> Version | None:
    found = [
        tuple(int(p) for p in match.groups() if p is not None) for match in GLIBC.finditer(data)
    ]
    return max(found, default=None)


def embedded(path: Path) -> Iterator[tuple[str, bytes]]:
    """The ELF files bundled in a PyInstaller one-file binary."""
    from PyInstaller.archive.readers import CArchiveReader  # noqa: PLC0415 - build group only

    archive = CArchiveReader(str(path))
    for name in archive.toc:
        blob = archive.extract(name)
        if isinstance(blob, bytes) and blob.startswith(ELF):
            yield f"{path}!{name}", blob


def elf_files(paths: list[Path]) -> Iterator[tuple[str, bytes]]:
    for root in paths:
        files = sorted(p for p in root.rglob("*") if p.is_file()) if root.is_dir() else [root]
        for path in files:
            if path.is_symlink():
                continue
            data = path.read_bytes()
            if not data.startswith(ELF):
                continue
            yield str(path), data
            if PYINSTALLER_COOKIE in data:
                yield from embedded(path)


def check(limit: Version, paths: list[Path]) -> tuple[Version | None, list[str]]:
    """The highest version needed, and each file needing more than `limit`."""
    top: Version | None = None
    over = []
    for name, data in elf_files(paths):
        version = highest(data)
        if version is None:
            continue
        top = max(top, version) if top else version
        if version > limit:
            over.append(f"{name} needs glibc {show(version)}")
    return top, over


def main(args: list[str]) -> int:
    limit = parse(args[0])
    top, over = check(limit, [Path(arg) for arg in args[1:]])
    if top is None:
        print("error: no ELF file names a glibc version", file=sys.stderr)
        return 1
    print(f"highest glibc needed: {show(top)} (limit {show(limit)})")
    for line in over:
        print(f"error: {line}", file=sys.stderr)
    return 1 if over else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
