"""Keep ``tests/`` mirroring ``src/spoolhq/`` (see "Layout" in docs/testing.md), and the
decisions index matching ``docs/decisions/``."""

import base64
import importlib.util
import json
import shutil
import subprocess
import sys
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


# The launch test of the built app (scripts/smoke_app.py, docs/packaging.md).

smoke_app = _script("smoke_app")


class _App:
    def __init__(self, code: int | None = None) -> None:
        self.code = code

    def poll(self) -> int | None:
        return self.code


def _healthy() -> object:
    return {"status": "ok", "service": "spoolhq"}


def _silent() -> object:
    raise ConnectionRefusedError


@pytest.fixture
def fast(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(smoke_app, "POLL_S", 0.01)


def test_the_launch_test_passes_a_clean_run(fast: None, capsys: Any) -> None:
    app = _App()
    smoke_app.wait_for_health(app, lambda: "log line", _healthy, timeout=1)
    smoke_app.stay_alive(app, lambda: "log line", seconds=0.05)
    gone = iter([{7: "spoolhq"}, {}])
    smoke_app.wait_for_cleanup({1}, lambda: next(gone), timeout=1)
    out = capsys.readouterr().out
    assert "ok   GET /api/health" in out
    assert "ok   no SpoolHQ process left" in out


def test_the_launch_test_fails_an_early_exit(fast: None) -> None:
    with pytest.raises(smoke_app.SmokeError, match="^the app exited early with code 101$"):
        smoke_app.wait_for_health(_App(101), lambda: "", _silent, timeout=1)


def test_the_launch_test_fails_a_panic(fast: None) -> None:
    output = "thread 'main' panicked at src/lib.rs:1:1:\nNo rustls crypto provider"
    with pytest.raises(smoke_app.SmokeError, match="^the app panicked$"):
        smoke_app.wait_for_health(_App(), lambda: output, _healthy, timeout=1)
    with pytest.raises(smoke_app.SmokeError, match="^the app panicked$"):
        smoke_app.stay_alive(_App(), lambda: output, seconds=0.05)


def test_the_launch_test_fails_without_health(fast: None) -> None:
    with pytest.raises(
        smoke_app.SmokeError, match=r"^no answer from GET /api/health within 0\.05 s$"
    ):
        smoke_app.wait_for_health(_App(), lambda: "", _silent, timeout=0.05)


def test_the_launch_test_fails_another_service(fast: None) -> None:
    with pytest.raises(
        smoke_app.SmokeError, match="^GET /api/health answered service 'other', not \"spoolhq\"$"
    ):
        smoke_app.wait_for_health(_App(), lambda: "", lambda: {"service": "other"}, timeout=1)


def test_the_launch_test_fails_leftover_processes(fast: None) -> None:
    left = {1: "spoolhq", 42: "spoolhq-desktop"}
    with pytest.raises(
        smoke_app.SmokeError,
        match=r"^SpoolHQ processes still running after 0\.05 s: spoolhq-desktop \(42\)$",
    ):
        smoke_app.wait_for_cleanup({1}, lambda: left, timeout=0.05)


def test_the_launch_test_lists_spoolhq_processes() -> None:
    # This test runs in Python, so none of the listed processes is this one.
    assert all("spoolhq" in name.lower() for name in smoke_app.spoolhq_processes().values())


# The benchmark score (scripts/bench_score.py, docs/benchmarks/README.md).

JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" tests="4">
<testcase classname="suite.test_a" name="test_one"><properties>
<property name="req" value="R01,R02" /><property name="import_s" value="0.5" />
</properties></testcase>
<testcase classname="suite.test_a" name="test_two"><properties>
<property name="req" value="R02" /></properties>
<failure message="boom">assert 1 == 2</failure></testcase>
<testcase classname="suite.test_b" name="test_three"><properties>
<property name="req" value="R10" /></properties>
<error message="setup">NotImplementedError</error></testcase>
<testcase classname="suite.test_b" name="test_four"><properties>
<property name="req" value="R10" /></properties><skipped message="no" /></testcase>
</testsuite></testsuites>
"""


def _bench_score() -> Any:
    return _script("bench_score")


def test_bench_score_reads_the_suite_report_by_requirement(tmp_path: Path) -> None:
    score = _bench_score()
    (tmp_path / "suite.xml").write_text(JUNIT, encoding="utf-8")
    cases = score.read_junit(tmp_path / "suite.xml")
    assert [c.outcome for c in cases] == ["passed", "failed", "error", "skipped"]
    assert cases[0].reqs == ("R01", "R02") and cases[0].props == {"import_s": "0.5"}
    assert score.by_requirement(cases) == {"R01": (1, 1), "R02": (1, 2), "R10": (0, 2)}


def _fake_run_log(workspace: Path) -> None:
    from spoolhq.services.runs.db import connect

    conn = connect(workspace)
    t = "2026-11-28T10:{:02d}:00.000Z".format
    runs = [  # id, ticket, kind, status, start, end
        (1, "plan", "plan", "done", t(0), t(2)),
        (2, "T01", "ticket", "done", t(2), t(5)),
        (3, "T02", "ticket", "done", t(5), t(15)),
        (4, "T03", "ticket", "blocked", t(15), t(20)),
    ]
    attempts = [  # run, ticket, number, status, input, output, cost (micro-USD)
        (1, "plan", 1, "approved", 1000, 100, 500_000),
        (2, "T01", 1, "approved", 2000, 200, 250_000),
        (3, "T02", 1, "gates_failed", 3000, 300, 250_000),
        (3, "T02", 2, "changes_requested", 100, 10, None),
        (3, "T02", 3, "approved", 100, 10, None),
        (4, "T03", 1, "needs_human", 10, 1, None),
    ]
    events = [
        (3, "log", {"message": "approved by the user", "approved_attempt": 5}),
        (4, "run.status", {"from": "running", "to": "blocked", "reason": "needs a person"}),
        (4, "log", {"message": "unblocked by the user", "user_note": "go"}),
        (1, "run.status", {"from": "running", "to": "blocked", "reason": "plan runs don't count"}),
    ]
    for run_id, ticket, kind, status, start, end in runs:
        conn.execute(
            "INSERT INTO runs (id, ticket_id, kind, status, daemon_instance, started_at, ended_at)"
            " VALUES (?, ?, ?, ?, 'x', ?, ?)",
            (run_id, ticket, kind, status, start, end),
        )
    for run_id, ticket, number, status, tokens_in, tokens_out, cost in attempts:
        conn.execute(
            "INSERT INTO attempts (run_id, ticket_id, number, kind, status, dir, input_tokens,"
            " output_tokens, cost_micro_usd, started_at)"
            " VALUES (?, ?, ?, 'initial', ?, 'd', ?, ?, ?, ?)",
            (run_id, ticket, number, status, tokens_in, tokens_out, cost, t(0)),
        )
    for run_id, kind, payload in events:
        conn.execute(
            "INSERT INTO events (run_id, ts, kind, payload) VALUES (?, ?, ?, ?)",
            (run_id, t(0), kind, json.dumps(payload)),
        )
    conn.close()


def test_bench_score_reads_the_process_numbers_from_the_run_log(tmp_path: Path) -> None:
    score = _bench_score()
    _fake_run_log(tmp_path)
    p = score.process_numbers(tmp_path)
    assert (p.tickets, p.done, p.first_try) == (3, 2, 1)
    assert p.retries == {"T01": 0, "T02": 2, "T03": 0}
    assert p.verdicts == {"approved": 2, "changes_requested": 1, "needs_human": 1}
    assert p.blocked == ["T03"]
    assert (p.approvals, p.unblocks, p.rejections) == (1, 1, 0)
    assert (p.input_tokens, p.output_tokens) == (6210, 621)
    assert p.cost_usd == pytest.approx(1.0)
    assert (p.run_seconds, p.wall_seconds) == (1200.0, 1200.0)


def test_bench_score_summary_has_the_totals(tmp_path: Path) -> None:
    score = _bench_score()
    (tmp_path / "suite.xml").write_text(JUNIT, encoding="utf-8")
    _fake_run_log(tmp_path)
    checks = [
        score.Check("hidden suite", "pytest", False, 1.0, "suite output"),
        score.Check("lint", "make lint", True, 2.0, ""),
        score.Check("tests", "make test", False, 3.0, "1 failed"),
    ]
    sizes = (12, ["big.py: 600 lines, over the 500-line limit"])
    cases = score.read_junit(tmp_path / "suite.xml")
    text = score.render("app", cases, checks, 91.5, sizes, score.process_numbers(tmp_path))
    for line in (
        "**Hidden suite: 1 of 4 tests passed (25.0%)**; 1 failed, 1 error, 1 skipped",
        "| R02 | 1 | 2 |",
        "| import_s | 0.5 |",
        "| lint | pass | 2.0 s | `make lint` |",
        "| tests | FAIL | 3.0 s | `make test` |",
        "- Coverage: 91.5%",
        "- Files over 500 lines: 1 of 12",
        "- Tickets: 3 run, 2 done, 1 passed first try",
        "- Retries: 2 (T02 2)",
        "- Blocked tickets: 1 (T03)",
        "- User approvals: 1; unblocks: 1; rejections: 0",
        "- Tokens: 6210 in (0 from cache), 621 out; cost $1.00",
        "- Time: 20.0 min in runs, 20.0 min first to last",
        "- failed: `suite.test_a::test_two` (R02)",
    ):
        assert line in text, line
    assert "hidden suite |" not in text  # the suite is scored above, not as a health check
    assert "suite output" not in text  # its report was read, so its output isn't needed


def test_bench_score_reads_a_coverage_total() -> None:
    score = _bench_score()
    output = "Name  Stmts  Miss  Cover\napp/x.py  10  1  90%\nTOTAL  120  6  95%\n"
    assert score.coverage_percent(output) == 95.0
    assert score.coverage_percent("3 passed") is None


@pytest.mark.integration
def test_bench_score_runs_a_suite_and_the_apps_commands(tmp_path: Path) -> None:
    score = _bench_score()
    app, suite = tmp_path / "app", tmp_path / "suite"
    app.mkdir()
    suite.mkdir()
    (app / "big.py").write_text("x = 1\n" * 501, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=app, check=True)  # noqa: S607
    subprocess.run(["git", "add", "big.py"], cwd=app, check=True)  # noqa: S607
    (suite / "test_s.py").write_text(
        "import os\n"
        "def test_app(record_property):\n"
        "    record_property('req', 'R01')\n"
        "    assert os.path.isdir(os.environ['BENCH_APP'])\n",
        encoding="utf-8",
    )
    out = tmp_path / "score.md"
    py = Path(sys.executable).as_posix()
    argv = [str(app), str(tmp_path / "adapter.py"), str(suite), "--out", str(out)]
    argv += ["--lint", f"{py} -c pass", "--test", f"{py} -c 'print(\"TOTAL 9 1 88%\")'"]
    assert score.main(argv) == 0
    text = out.read_text(encoding="utf-8")
    assert "**Hidden suite: 1 of 1 tests passed (100.0%)**" in text
    assert "| R01 | 1 | 1 |" in text
    assert "- Coverage: 88%" in text
    assert "- Files over 500 lines: 1 of 1" in text
