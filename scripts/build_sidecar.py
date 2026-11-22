"""Build the `spool` CLI as one file for the desktop app's sidecar (docs/packaging.md).

Run as `just build-daemon` (or `uv run --directory daemon --group build python
../scripts/build_sidecar.py`). Writes `desktop/src-tauri/binaries/spoolhq-<target triple>`
(`.exe` on Windows), the name Tauri's `externalBin` expects, then fails if the binary
contains `spoolhq.devtools` or its scenarios.
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "daemon" / "src" / "spoolhq"
BINARIES = ROOT / "desktop" / "src-tauri" / "binaries"
WORK = ROOT / "daemon" / "build" / "pyinstaller"

# Package data the daemon reads at run time: built-in templates and prompt files.
DATA = ("templates", "services/context/prompts")
EXCLUDED = ("spoolhq.devtools",)
FORBIDDEN = ("spoolhq.devtools", "spoolhq/devtools", "spoolhq\\devtools")

TRIPLES = {
    ("Linux", "x86_64"): "x86_64-unknown-linux-gnu",
    ("Linux", "aarch64"): "aarch64-unknown-linux-gnu",
    ("Darwin", "x86_64"): "x86_64-apple-darwin",
    ("Darwin", "arm64"): "aarch64-apple-darwin",
    ("Windows", "AMD64"): "x86_64-pc-windows-msvc",
    ("Windows", "ARM64"): "aarch64-pc-windows-msvc",
}


def host_triple() -> str:
    key = (platform.system(), platform.machine())
    if key not in TRIPLES:
        sys.exit(f"error: no target triple for {key}; pass --target")
    return TRIPLES[key]


def pyinstaller_args(name: str) -> list[str]:
    """PyInstaller's arguments: one file, the package data, dev tools left out."""
    sep = ";" if sys.platform == "win32" else ":"
    args = [
        "--onefile",
        "--noconfirm",
        "--clean",
        "--log-level=WARN",
        f"--name={name}",
        f"--distpath={BINARIES}",
        f"--workpath={WORK}",
        f"--specpath={WORK}",
        # uvicorn picks its protocol and loop modules by name.
        "--collect-submodules=uvicorn",
        # Copier loads its default Jinja extension by name.
        "--hidden-import=jinja2_ansible_filters",
        "--copy-metadata=keyring",
    ]
    args += [f"--add-data={PACKAGE / part}{sep}spoolhq/{part}" for part in DATA]
    args += [f"--exclude-module={module}" for module in EXCLUDED]
    return [*args, str(PACKAGE / "__main__.py")]


def binary_path(triple: str) -> Path:
    suffix = ".exe" if "windows" in triple else ""
    return BINARIES / f"spoolhq-{triple}{suffix}"


def forbidden_entries(listing: str) -> list[str]:
    """Lines of the archive listing that name the dev tools."""
    return [line.strip() for line in listing.splitlines() if any(f in line for f in FORBIDDEN)]


def check_no_devtools(binary: Path) -> None:
    listing = subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [
            sys.executable,
            "-m",
            "PyInstaller.utils.cliutils.archive_viewer",
            "--list",
            "--recursive",
            "--brief",
            str(binary),
        ],
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout
    if "spoolhq.cli.main" not in listing:
        sys.exit(f"error: cannot read the module list of {binary}")
    if found := forbidden_entries(listing):
        sys.exit(f"error: {binary} contains dev tools: {', '.join(found[:5])}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="Rust target triple (default: this machine's)")
    parser.add_argument(
        "--placeholder",
        action="store_true",
        help="only create an empty file if none exists, so the Rust side builds without it",
    )
    options = parser.parse_args()
    triple = options.target or host_triple()
    binary = binary_path(triple)
    if options.placeholder:
        BINARIES.mkdir(parents=True, exist_ok=True)
        binary.touch()
        print(f"{binary} ({binary.stat().st_size} bytes)")
        return
    subprocess.run(  # noqa: S603 - fixed argument list, no shell
        [sys.executable, "-m", "PyInstaller", *pyinstaller_args(binary.stem)], check=True
    )
    check_no_devtools(binary)
    print(f"{binary} ({binary.stat().st_size / 1_000_000:.1f} MB)")


if __name__ == "__main__":
    main()
