"""Release helpers for `release.yml` and `just set-version` (docs/packaging.md).

- `set-version <x.y.z>`: writes the version to the daemon package, `desktop/package.json`
  and `tauri.conf.json` (the recipe then runs `uv lock` for `daemon/uv.lock`).
- `check-tag <tag>`: fails unless the three agree, the tag is `v<version>` and the
  update public key is set.
- `collect <target triple> <out>`: copies this OS's installers out of Tauri's bundle
  folder with unique names and writes `latest-<platform>.json` for its update artifact.
- `merge <out> <notes file> <feed>...`: one `latest.json` from the per-platform feeds.
- `check-feed <latest.json> <platform>...`: each platform listed with a URL and a
  signature made by the key in `tauri.conf.json` (when one is set).
"""

import base64
import json
import os
import re
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = Path("daemon/pyproject.toml")
PACKAGE_JSON = Path("desktop/package.json")
TAURI_CONF = Path("desktop/src-tauri/tauri.conf.json")
BUNDLE = Path("desktop/src-tauri/target/release/bundle")
DOWNLOAD = "https://github.com/ATOM43/Spoolhq/releases/download/v{version}/{name}"
SEMVER = re.compile(r"\d+\.\d+\.\d+")
# The first `version` line of each file: [project] in pyproject, top level in the JSON.
VERSION_LINES = {
    PYPROJECT: re.compile(r'^(version = ")([^"]*)(")', re.MULTILINE),
    PACKAGE_JSON: re.compile(r'^(  "version": ")([^"]*)(")', re.MULTILINE),
    TAURI_CONF: re.compile(r'^(  "version": ")([^"]*)(")', re.MULTILINE),
}
# Per OS: the update platform key, the update artifact and every installer, as globs
# inside BUNDLE. macOS arm64 and x86_64 both make `SpoolHQ.app.tar.gz`, so the copy
# gets the architecture in its name.
PLATFORMS = {
    "x86_64-unknown-linux-gnu": ("linux-x86_64", "appimage/*.AppImage", ["deb/*.deb", "rpm/*.rpm"]),
    "x86_64-pc-windows-msvc": ("windows-x86_64", "nsis/*-setup.exe", []),
    "aarch64-apple-darwin": ("darwin-aarch64", "macos/*.app.tar.gz", ["dmg/*.dmg"]),
    "x86_64-apple-darwin": ("darwin-x86_64", "macos/*.app.tar.gz", ["dmg/*.dmg"]),
}


class ReleaseError(Exception):
    pass


def versions(root: Path) -> dict[Path, str]:
    found = {}
    for path, pattern in VERSION_LINES.items():
        match = pattern.search((root / path).read_text("utf-8"))
        if match is None:
            raise ReleaseError(f"No version in {path}")
        found[path] = match.group(2)
    return found


def set_version(root: Path, version: str) -> None:
    if not SEMVER.fullmatch(version):
        raise ReleaseError(f"Version {version} isn't x.y.z")
    for path, pattern in VERSION_LINES.items():
        text = (root / path).read_text("utf-8")
        new, count = pattern.subn(rf"\g<1>{version}\g<3>", text, count=1)
        if count != 1:
            raise ReleaseError(f"No version in {path}")
        (root / path).write_text(new, "utf-8")


def app_version(root: Path) -> str:
    found = versions(root)
    if len(set(found.values())) != 1:
        listed = ", ".join(f"{path} {version}" for path, version in found.items())
        raise ReleaseError(f"The app versions differ: {listed}; run just set-version")
    return found[TAURI_CONF]


def pubkey(root: Path) -> str:
    conf = json.loads((root / TAURI_CONF).read_text("utf-8"))
    return str(conf["plugins"]["updater"]["pubkey"])


def check_tag(root: Path, tag: str) -> None:
    version = app_version(root)
    if tag != f"v{version}":
        raise ReleaseError(f"Tag {tag} doesn't match the app version {version}")
    if not pubkey(root):
        raise ReleaseError("Put the update public key in tauri.conf.json; see docs/packaging.md")


def feed_entry(version: str, artifact: Path) -> dict[str, str]:
    sig = artifact.with_name(artifact.name + ".sig")
    if not sig.is_file():
        raise ReleaseError(f"No signature for {artifact.name}; is TAURI_SIGNING_PRIVATE_KEY set?")
    return {
        "signature": sig.read_text("utf-8").strip(),
        "url": DOWNLOAD.format(version=version, name=artifact.name),
    }


def feed(version: str, notes: str, pub_date: str, artifacts: dict[str, Path]) -> dict[str, object]:
    return {
        "version": version,
        "notes": notes,
        "pub_date": pub_date,
        # Read by T52, not enforced in v0.1.0.
        "minimum_version": "",
        "platforms": {key: feed_entry(version, path) for key, path in artifacts.items()},
    }


def only(folder: Path, pattern: str) -> Path:
    matches = sorted(folder.glob(pattern))
    if len(matches) != 1:
        raise ReleaseError(f"Expected one {pattern} in {folder}, found {len(matches)}")
    return matches[0]


def collect(root: Path, target: str, out: Path) -> Path:
    """Copy this OS's installers to `out`; return the per-platform feed's path."""
    version = app_version(root)
    key, update, installers = PLATFORMS[target]
    out.mkdir(parents=True, exist_ok=True)
    for pattern in installers:
        shutil.copy2(only(root / BUNDLE, pattern), out)
    artifact = only(root / BUNDLE, update)
    name = artifact.name
    if name.endswith(".app.tar.gz"):
        name = f"{name.removesuffix('.app.tar.gz')}_{version}_{key.split('-')[1]}.app.tar.gz"
    shutil.copy2(artifact, out / name)
    shutil.copy2(artifact.with_name(artifact.name + ".sig"), out / f"{name}.sig")
    path = out / f"latest-{key}.json"
    data = feed(version, "", now(), {key: out / name})
    path.write_text(json.dumps(data, indent=2) + "\n", "utf-8")
    return path


def merge(feeds: list[dict[str, Any]], notes: str, pub_date: str) -> dict[str, object]:
    platforms: dict[str, object] = {}
    for part in feeds:
        if part["version"] != feeds[0]["version"]:
            raise ReleaseError(f"Feeds for versions {feeds[0]['version']} and {part['version']}")
        platforms.update(part["platforms"])
    return {**feeds[0], "notes": notes, "pub_date": pub_date, "platforms": platforms}


def key_id(base64_text: str) -> bytes:
    """The 8-byte key id of a Tauri public key or `.sig` (base64 of a minisign file)."""
    lines = base64.b64decode(base64_text).decode("utf-8").splitlines()
    return base64.b64decode(lines[1])[2:10]


def check_feed(data: dict[str, object], platforms: list[str], public_key: str) -> None:
    listed = data.get("platforms")
    if not isinstance(listed, dict):
        raise ReleaseError("latest.json has no platforms")
    for key in platforms:
        entry = listed.get(key)
        if not isinstance(entry, dict) or not entry.get("url") or not entry.get("signature"):
            raise ReleaseError(f"latest.json has no URL and signature for {key}")
        if public_key and key_id(entry["signature"]) != key_id(public_key):
            raise ReleaseError(f"The {key} update isn't signed by the key in tauri.conf.json")


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(args: list[str]) -> None:
    command, rest = args[0], args[1:]
    if command == "set-version":
        set_version(ROOT, rest[0])
    elif command == "check-tag":
        check_tag(ROOT, rest[0])
    elif command == "collect":
        print(collect(ROOT, rest[0], Path(rest[1])))
    elif command == "merge":
        notes = Path(rest[1]).read_text("utf-8").strip()
        parts = [json.loads(Path(path).read_text("utf-8")) for path in rest[2:]]
        Path(rest[0]).write_text(json.dumps(merge(parts, notes, now()), indent=2) + "\n", "utf-8")
    elif command == "check-feed":
        # A dry run's throwaway key (release.yml's pubkey input) stands in for the file's.
        key = os.environ.get("UPDATER_PUBKEY") or pubkey(ROOT)
        check_feed(json.loads(Path(rest[0]).read_text("utf-8")), rest[1:], key)
    else:
        raise ReleaseError(f"Unknown command {command}")
    print(f"ok   {command} {' '.join(rest)}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ReleaseError as error:
        sys.exit(f"error: {error}")
