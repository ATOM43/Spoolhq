"""Keep ``tests/`` mirroring ``src/spoolhq/`` (see "Layout" in docs/testing.md), and the
decisions index matching ``docs/decisions/``."""

import base64
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from tests.conftest import FIXTURES_DIR, TESTS_DIR

PACKAGE_DIR = TESTS_DIR.parent / "src" / "spoolhq"


def folders() -> list[Path]:
    """Every folder under ``tests/`` except shared fixture data and caches."""
    return sorted(
        path
        for path in TESTS_DIR.rglob("*")
        if path.is_dir()
        and path != FIXTURES_DIR
        and FIXTURES_DIR not in path.parents
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    )


def test_no_test_files_directly_in_tests() -> None:
    stray = sorted(
        path.name for path in TESTS_DIR.glob("test_*.py") if path.name != Path(__file__).name
    )
    assert stray == [], f"move these into the folder that mirrors the code they test: {stray}"


def test_every_test_folder_mirrors_a_package() -> None:
    unmatched = [
        folder.relative_to(TESTS_DIR).as_posix()
        for folder in folders()
        if not (PACKAGE_DIR / folder.relative_to(TESTS_DIR)).is_dir()
    ]
    assert unmatched == [], f"no matching package under src/spoolhq/ for: {unmatched}"


def test_every_test_folder_has_init() -> None:
    missing = [
        folder.relative_to(TESTS_DIR.parent).as_posix()
        for folder in [TESTS_DIR, *folders()]
        if not (folder / "__init__.py").is_file()
    ]
    assert missing == [], f"add an empty __init__.py to: {missing}"


# DECISIONS.md and docs/decisions/ (scripts/check_decisions.py, run by `just lint`).


def _script(name: str) -> Any:
    path = TESTS_DIR.parents[1] / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _check_decisions() -> Any:
    return _script("check_decisions")


def _decisions(root: Path, index: list[str], entries: list[str]) -> Path:
    (root / "docs" / "decisions").mkdir(parents=True)
    (root / "DECISIONS.md").write_text("# Decisions\n\n" + "\n".join(index) + "\n", "utf-8")
    (root / "docs" / "decisions" / "core.md").write_text("\n".join(entries) + "\n", "utf-8")
    return root


GOOD_INDEX = ["001 · One · docs/decisions/core.md", "002 · Two. · docs/decisions/core.md"]
GOOD_ENTRIES = ["1. **One** (T01). Why.", "2. **Two.** Why."]


def test_the_repo_decisions_layout_is_consistent() -> None:
    assert _check_decisions().problems(TESTS_DIR.parents[1]) == []


def test_a_consistent_fixture_passes(tmp_path: Path) -> None:
    root = _decisions(tmp_path, GOOD_INDEX, GOOD_ENTRIES)
    assert _check_decisions().problems(root) == []


def test_a_missing_number_fails(tmp_path: Path) -> None:
    index = [GOOD_INDEX[0], "003 · Three · docs/decisions/core.md"]
    entries = [GOOD_ENTRIES[0], "3. **Three** Why."]
    found = _check_decisions().problems(_decisions(tmp_path, index, entries))
    assert found == ["DECISIONS.md: 2 is missing (numbers must have no gaps)"]


def test_an_entry_missing_from_the_area_files_fails(tmp_path: Path) -> None:
    found = _check_decisions().problems(_decisions(tmp_path, GOOD_INDEX, GOOD_ENTRIES[:1]))
    assert found == ["DECISIONS.md: 2 has no entry in docs/decisions/"]


def test_a_duplicated_number_fails(tmp_path: Path) -> None:
    index = [*GOOD_INDEX, GOOD_INDEX[1]]
    entries = [*GOOD_ENTRIES, GOOD_ENTRIES[1]]
    found = _check_decisions().problems(_decisions(tmp_path, index, entries))
    assert "DECISIONS.md: 2 is listed 2 times" in found
    assert "docs/decisions: 2 has 2 entries" in found


def test_a_mismatched_title_fails(tmp_path: Path) -> None:
    index = [GOOD_INDEX[0], "002 · Two · docs/decisions/core.md"]
    found = _check_decisions().problems(_decisions(tmp_path, index, GOOD_ENTRIES))
    assert found == ["DECISIONS.md: 2 title 'Two' != heading 'Two.'"]


# The 500-line limit (scripts/check_line_limit.py, run by `just lint`).


def test_the_repo_is_within_the_line_limit() -> None:
    assert _script("check_line_limit").oversized(TESTS_DIR.parents[1]) == []


def test_a_rust_file_over_the_limit_fails(tmp_path: Path) -> None:
    folder = tmp_path / "desktop" / "src-tauri" / "src"
    folder.mkdir(parents=True)
    (folder / "short.rs").write_text("fn a() {}\n" * 500, encoding="utf-8")
    (folder / "long.rs").write_text("fn a() {}\n" * 501, encoding="utf-8")
    found = _script("check_line_limit").oversized(tmp_path)
    assert found == [("desktop/src-tauri/src/long.rs", 501)]


def _progress(root: Path, entries: int) -> Path:
    body = "".join(f"## Entry {n}\n\nDone.\n\n" for n in range(entries))
    (root / "PROGRESS.md").write_text(
        f"# Progress\n\n## What exists\n\nStuff.\n\n{body}", encoding="utf-8"
    )
    return root


def test_the_repo_progress_holds_at_most_five_recent_entries() -> None:
    assert _check_decisions().progress_problems(TESTS_DIR.parents[1]) == []


def test_five_recent_progress_entries_pass(tmp_path: Path) -> None:
    assert _check_decisions().progress_problems(_progress(tmp_path, 5)) == []


def test_six_recent_progress_entries_fail(tmp_path: Path) -> None:
    assert _check_decisions().progress_problems(_progress(tmp_path, 6)) == [
        "PROGRESS.md has 6 recent entries; move the oldest to docs/progress-archive.md"
    ]


# The sidecar build (scripts/build_sidecar.py, docs/packaging.md).


def _build_sidecar() -> Any:
    return _script("build_sidecar")


def test_pyinstaller_leaves_out_devtools_and_takes_the_package_data() -> None:
    args = _build_sidecar().pyinstaller_args("spoolhq-x86_64-unknown-linux-gnu")
    assert "--exclude-module=spoolhq.devtools" in args
    assert "--onefile" in args
    data = [arg for arg in args if arg.startswith("--add-data=")]
    assert len(data) == 2
    assert any(arg.endswith("spoolhq/templates") for arg in data)
    assert any(arg.endswith("spoolhq/services/context/prompts") for arg in data)
    assert not any("devtools" in arg for arg in data)
    assert not any(arg.startswith("--collect-submodules=spoolhq") for arg in args)


def test_forbidden_entries_find_devtools_modules_and_scenarios() -> None:
    listing = "\n".join(
        [
            " spoolhq.cli.main",
            " spoolhq.devtools.fake_runner",
            " spoolhq/devtools/scenarios/happy.json",
            " spoolhq/templates/fastapi-react/copier.yml",
        ]
    )
    assert _build_sidecar().forbidden_entries(listing) == [
        "spoolhq.devtools.fake_runner",
        "spoolhq/devtools/scenarios/happy.json",
    ]
    assert _build_sidecar().forbidden_entries(" spoolhq.cli.main\n") == []


def test_binary_names_follow_the_sidecar_convention() -> None:
    linux = _build_sidecar().binary_path("x86_64-unknown-linux-gnu")
    windows = _build_sidecar().binary_path("x86_64-pc-windows-msvc")
    assert linux.name == "spoolhq-x86_64-unknown-linux-gnu"
    assert windows.name == "spoolhq-x86_64-pc-windows-msvc.exe"
    assert linux.parent.parts[-3:] == ("desktop", "src-tauri", "binaries")


# The release helpers (scripts/release.py, docs/packaging.md).

REPO = TESTS_DIR.parents[1]


# Loaded once, so ReleaseError is one class across the tests.
release = _script("release")
VERSIONED = ("daemon/pyproject.toml", "desktop/package.json", "desktop/src-tauri/tauri.conf.json")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """A copy of the three versioned files."""
    for path in VERSIONED:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / path, tmp_path / path)
    return tmp_path


def _minisign(key_id: bytes, extra: bytes) -> str:
    """A Tauri-style base64 public key or signature with the given key id."""
    line = base64.b64encode(b"Ed" + key_id + extra).decode()
    return base64.b64encode(f"untrusted comment: x\n{line}\n".encode()).decode()


def test_set_version_updates_all_three_files(root: Path) -> None:
    release.set_version(root, "0.1.0")
    assert set(release.versions(root).values()) == {"0.1.0"}
    assert json.loads((root / "desktop/package.json").read_text("utf-8"))["version"] == "0.1.0"
    conf = json.loads((root / "desktop/src-tauri/tauri.conf.json").read_text("utf-8"))
    assert conf["version"] == "0.1.0"
    # Only the package's own version changes, not a dependency's or the tool versions.
    pyproject = (root / "daemon/pyproject.toml").read_text("utf-8")
    assert pyproject.count('version = "0.1.0"') == 1
    assert release.app_version(root) == "0.1.0"


def test_set_version_refuses_a_non_semver(root: Path) -> None:
    with pytest.raises(release.ReleaseError, match="isn't x.y.z"):
        release.set_version(root, "v0.1")


def test_a_tag_that_doesnt_match_the_app_version_fails(root: Path) -> None:
    release.set_version(root, "0.0.9")
    with pytest.raises(
        release.ReleaseError, match="^Tag v0.1.0 doesn't match the app version 0.0.9$"
    ):
        release.check_tag(root, "v0.1.0")


def test_versions_that_differ_fail(root: Path) -> None:
    release.set_version(root, "0.1.0")
    package = root / "desktop/package.json"
    package.write_text(package.read_text("utf-8").replace('"0.1.0"', '"0.0.9"', 1), "utf-8")
    with pytest.raises(release.ReleaseError, match="The app versions differ"):
        release.check_tag(root, "v0.1.0")


def test_a_matching_tag_needs_the_public_key(root: Path) -> None:
    conf_path = root / "desktop/src-tauri/tauri.conf.json"
    conf = json.loads(conf_path.read_text("utf-8"))
    conf["version"] = "0.1.0"
    for key in ("", _minisign(b"k" * 8, b"p" * 32)):
        conf["plugins"]["updater"]["pubkey"] = key
        conf_path.write_text(json.dumps(conf, indent=2), "utf-8")
        release.set_version(root, "0.1.0")
        if key:
            with pytest.raises(release.ReleaseError, match="Use an annotated tag"):
                release.check_tag(root, "v0.1.0")
        else:
            with pytest.raises(release.ReleaseError, match="Put the update public key"):
                release.check_tag(root, "v0.1.0")


ANNOTATE = 'Use an annotated tag with release notes: git tag -a v0.1.0 -m "…"'


def test_a_tag_without_a_message_fails_with_how_to_annotate() -> None:
    for kind, message in [("commit", "the commit's message\n"), ("tag", " \n"), ("", "")]:
        with pytest.raises(release.ReleaseError) as raised:
            release.check_annotated("v0.1.0", kind, message)
        assert str(raised.value) == ANNOTATE
    release.check_annotated("v0.1.0", "tag", "First release\n")


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)  # noqa: S603, S607


def test_the_tag_message_is_read_from_git(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(
        tmp_path,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        "c",
    )
    _git(tmp_path, "tag", "v0.1.0")
    _git(
        tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "tag", "-a", "v0.2.0", "-m", "Notes"
    )
    assert release.tag_message(tmp_path, "v0.1.0")[0] == "commit"
    kind, message = release.tag_message(tmp_path, "v0.2.0")
    assert (kind, message.strip()) == ("tag", "Notes")


def _artifact(folder: Path, name: str, signature: str | None) -> Path:
    path = folder / name
    path.write_bytes(b"bundle")
    if signature is not None:
        path.with_name(name + ".sig").write_text(signature + "\n", "utf-8")
    return path


def test_feed_lists_each_platform_with_its_url_and_signature(tmp_path: Path) -> None:
    artifacts = {
        "linux-x86_64": _artifact(tmp_path, "SpoolHQ_0.1.0_amd64.AppImage", "sig-linux"),
        "windows-x86_64": _artifact(tmp_path, "SpoolHQ_0.1.0_x64-setup.exe", "sig-win"),
    }
    data = release.feed("0.1.0", "Notes", "2026-11-23T10:00:00Z", artifacts)
    download = "https://github.com/ATOM43/Spoolhq/releases/download/v0.1.0/"
    assert data == {
        "version": "0.1.0",
        "notes": "Notes",
        "pub_date": "2026-11-23T10:00:00Z",
        "minimum_version": "",
        "platforms": {
            "linux-x86_64": {
                "signature": "sig-linux",
                "url": download + "SpoolHQ_0.1.0_amd64.AppImage",
            },
            "windows-x86_64": {
                "signature": "sig-win",
                "url": download + "SpoolHQ_0.1.0_x64-setup.exe",
            },
        },
    }


def test_feed_without_a_signature_fails(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path, "SpoolHQ_0.1.0_x64-setup.exe", None)
    with pytest.raises(release.ReleaseError, match="No signature for SpoolHQ_0.1.0_x64-setup"):
        release.feed("0.1.0", "", "2026-11-23T10:00:00Z", {"windows-x86_64": artifact})


def test_collect_names_the_mac_update_by_architecture(root: Path) -> None:
    bundle = root / "desktop/src-tauri/target/release/bundle"
    (bundle / "macos").mkdir(parents=True)
    (bundle / "dmg").mkdir()
    _artifact(bundle / "macos", "SpoolHQ.app.tar.gz", "sig-mac")
    _artifact(bundle / "dmg", "SpoolHQ_0.0.0_aarch64.dmg", None)
    feed_path = release.collect(root, "aarch64-apple-darwin", root / "dist")
    assert sorted(path.name for path in (root / "dist").iterdir()) == [
        "SpoolHQ_0.0.0_aarch64.app.tar.gz",
        "SpoolHQ_0.0.0_aarch64.app.tar.gz.sig",
        "SpoolHQ_0.0.0_aarch64.dmg",
        "latest-darwin-aarch64.json",
    ]
    entry = json.loads(feed_path.read_text("utf-8"))["platforms"]["darwin-aarch64"]
    assert entry["url"].endswith("/v0.0.0/SpoolHQ_0.0.0_aarch64.app.tar.gz")
    assert entry["signature"] == "sig-mac"


def test_collect_fails_when_an_installer_is_missing(root: Path) -> None:
    (root / "desktop/src-tauri/target/release/bundle/nsis").mkdir(parents=True)
    with pytest.raises(release.ReleaseError, match="Expected one nsis/\\*-setup.exe"):
        release.collect(root, "x86_64-pc-windows-msvc", root / "dist")


def _part(key: str, version: str = "0.1.0") -> dict[str, Any]:
    return {
        "version": version,
        "notes": "",
        "pub_date": "x",
        "minimum_version": "",
        "platforms": {key: {"url": f"https://x/{key}", "signature": "s"}},
    }


def test_merge_combines_platforms_and_sets_the_notes() -> None:
    data = release.merge([_part("linux-x86_64"), _part("darwin-aarch64")], "Notes", "now")
    assert set(data["platforms"]) == {"linux-x86_64", "darwin-aarch64"}
    assert data["notes"] == "Notes"
    assert data["pub_date"] == "now"
    with pytest.raises(release.ReleaseError, match="Feeds for versions"):
        release.merge([_part("linux-x86_64"), _part("darwin-aarch64", "0.2.0")], "", "now")


def test_check_feed_needs_each_platform_signed_by_the_configured_key() -> None:
    key = _minisign(b"A" * 8, b"p" * 32)
    data = _part("linux-x86_64")
    data["platforms"]["linux-x86_64"]["signature"] = _minisign(b"A" * 8, b"s" * 64)
    release.check_feed(data, ["linux-x86_64"], key)
    release.check_feed(data, ["linux-x86_64"], "")
    with pytest.raises(release.ReleaseError, match="no URL and signature for windows-x86_64"):
        release.check_feed(data, ["windows-x86_64"], key)
    with pytest.raises(release.ReleaseError, match="isn't signed by the key"):
        release.check_feed(data, ["linux-x86_64"], _minisign(b"B" * 8, b"p" * 32))


# The glibc check for the Linux build (scripts/check_glibc.py, docs/packaging.md).

check_glibc = _script("check_glibc")


def _elf(path: Path, *versions: str) -> Path:
    """A stand-in binary: the ELF magic and the version names a linker would leave."""
    names = b"\0".join(f"GLIBC_{v}".encode() for v in versions)
    path.write_bytes(b"\x7fELF\x02\x01\x01" + b"\0" * 32 + b"libc.so.6\0" + names + b"\0")
    return path


def test_the_glibc_check_passes_a_binary_needing_2_31(tmp_path: Path, capsys: Any) -> None:
    _elf(tmp_path / "spoolhq", "2.2.5", "2.17", "2.31")
    (tmp_path / "notes.txt").write_text("GLIBC_2.99 in a text file is ignored", "utf-8")
    assert check_glibc.main(["2.35", str(tmp_path)]) == 0
    assert "highest glibc needed: 2.31 (limit 2.35)" in capsys.readouterr().out


def test_the_glibc_check_fails_a_binary_needing_2_39(tmp_path: Path, capsys: Any) -> None:
    _elf(tmp_path / "old", "2.31")
    _elf(tmp_path / "new", "2.34", "2.39")
    assert check_glibc.main(["2.35", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "new needs glibc 2.39" in err
    assert "old" not in err.replace(str(tmp_path), "")


def test_the_glibc_check_fails_when_it_finds_no_binary(tmp_path: Path) -> None:
    assert check_glibc.main(["2.35", str(tmp_path)]) == 1
