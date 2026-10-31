"""The code graph cache: full build, incremental update, atomic save, rebuild, failures."""

import json
import logging
import os
import sys
from pathlib import Path

import pytest

from spoolhq.core.daemon_lock import acquire_lock
from spoolhq.services.codegraph import cache, tool
from spoolhq.services.codegraph.cache import POINTER, cache_dir, refresh
from spoolhq.services.codegraph.tool import Graphify, GraphifyError, find_command, probe
from tests.conftest import FakeGraphify


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "checkout"
    path.mkdir()
    (path / "hello.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    return path


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    path = tmp_path / "workspace"
    path.mkdir()
    return path


def pointer(workspace: Path) -> dict[str, str]:
    data: dict[str, str] = json.loads((cache_dir(workspace) / POINTER).read_text("utf-8"))
    return data


def builds(workspace: Path) -> list[str]:
    return sorted(p.name for p in cache_dir(workspace).iterdir() if p.is_dir())


@pytest.mark.integration
def test_first_a_full_build_then_updates_against_the_saved_cache(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    first = refresh(source, workspace)
    assert first is not None
    assert first.kind == "full"
    assert first.text.startswith("## Summary\n")
    assert pointer(workspace)["version"] == "0.9.92"
    assert builds(workspace) == [pointer(workspace)["build"]]

    second = refresh(source, workspace)
    assert second is not None
    assert second.kind == "update"
    assert fake_graphify.commands() == ["full", "cluster", "update", "cluster"]
    # Graphify runs with --out in the cache, from the cache: nothing lands in the checkout.
    assert sorted(p.name for p in source.iterdir()) == ["hello.py"]
    for call in fake_graphify.calls()[1:]:
        if call["command"] != "version":
            assert Path(call["cwd"]).parent == cache_dir(workspace)
    update = fake_graphify.calls()[-2]["argv"]
    assert update[:3] == ["extract", str(source), "--code-only"]
    assert "--force" not in update
    assert builds(workspace) == [pointer(workspace)["build"]]  # the old build is gone


@pytest.mark.integration
def test_a_failing_update_deletes_the_cache_and_rebuilds_once(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    refresh(source, workspace)
    old = pointer(workspace)["build"]
    fake_graphify.configure(fail=["update"])

    rebuilt = refresh(source, workspace)

    assert rebuilt is not None
    assert rebuilt.kind == "full"
    assert fake_graphify.commands()[2:] == ["update", "full", "cluster"]
    assert pointer(workspace)["build"] != old
    assert builds(workspace) == [pointer(workspace)["build"]]


@pytest.mark.integration
def test_a_failing_rebuild_carries_on_without_a_map(
    fake_graphify: FakeGraphify,
    source: Path,
    workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    refresh(source, workspace)
    fake_graphify.configure(fail=["update", "full"])

    with caplog.at_level(logging.INFO):
        assert refresh(source, workspace) is None

    assert fake_graphify.commands()[2:] == ["update", "full"]
    assert not (cache_dir(workspace) / POINTER).exists()
    assert builds(workspace) == []
    assert "no code map: graphify extract exited with code 1" in caplog.text


@pytest.mark.integration
def test_a_failing_report_is_a_failed_build(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    fake_graphify.configure(fail=["cluster"])
    assert refresh(source, workspace) is None
    assert builds(workspace) == []


@pytest.mark.integration
def test_a_cache_from_another_version_is_discarded(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    fake_graphify.configure(version="0.9.80")
    refresh(source, workspace)
    assert pointer(workspace)["version"] == "0.9.80"

    fake_graphify.configure()  # back to 0.9.92
    rebuilt = refresh(source, workspace)

    assert rebuilt is not None
    assert rebuilt.kind == "full"
    assert pointer(workspace)["version"] == "0.9.92"
    assert len(builds(workspace)) == 1


@pytest.mark.integration
def test_a_crash_while_saving_leaves_the_previous_cache(
    fake_graphify: FakeGraphify,
    source: Path,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    refresh(source, workspace)
    before = pointer(workspace)

    def crash(*_args: object) -> None:
        raise KeyboardInterrupt  # the process dies between the rename and the pointer

    with monkeypatch.context() as patch:
        patch.setattr(cache.os, "replace", crash)
        with pytest.raises(KeyboardInterrupt):
            refresh(source, workspace)

    assert pointer(workspace) == before
    assert (cache_dir(workspace) / before["build"] / "graphify-out" / "graph.json").is_file()
    after = refresh(source, workspace)  # the next refresh updates from it, and tidies up
    assert after is not None
    assert after.kind == "update"
    assert builds(workspace) == [pointer(workspace)["build"]]
    assert [p.name for p in cache_dir(workspace).iterdir() if p.name.endswith(".tmp")] == []


@pytest.mark.integration
def test_a_save_error_still_returns_the_map(
    fake_graphify: FakeGraphify,
    source: Path,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_args: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(cache.os, "replace", fail)
    built = refresh(source, workspace)
    assert built is not None
    assert not (cache_dir(workspace) / POINTER).exists()


def test_without_graphify_one_note_and_no_map(
    source: Path, workspace: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="spoolhq.services.codegraph"):
        assert refresh(source, workspace) is None
    assert [r.getMessage() for r in caplog.records] == [
        "no code map: graphify is not on PATH or its version can't be read"
    ]
    assert not cache_dir(workspace).exists()


@pytest.mark.integration
def test_an_unreadable_version_counts_as_missing(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    fake_graphify.configure(version="")
    assert probe() is None
    assert refresh(source, workspace) is None
    assert fake_graphify.commands() == []


@pytest.mark.integration
def test_an_untested_version_warns_and_still_builds(
    fake_graphify: FakeGraphify,
    source: Path,
    workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_graphify.configure(version="0.10.1")
    with caplog.at_level(logging.WARNING):
        assert refresh(source, workspace) is not None
    assert "graphify 0.10.1 is untested; SpoolHQ is tested with 0.9.92" in caplog.text


@pytest.mark.integration
def test_a_hanging_graphify_is_stopped_at_the_timeout(
    fake_graphify: FakeGraphify,
    source: Path,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tool, "TIMEOUT_S", 1.0)
    fake_graphify.configure(sleep=60)
    assert refresh(source, workspace) is None
    assert builds(workspace) == []


@pytest.mark.integration
def test_a_busy_cache_gives_no_map(
    fake_graphify: FakeGraphify, source: Path, workspace: Path
) -> None:
    with acquire_lock(cache_dir(workspace) / "lock"):
        assert refresh(source, workspace) is None
    assert fake_graphify.commands() == []


def test_find_command_uses_path() -> None:
    assert find_command(lambda name: f"/opt/{name}") == ["/opt/graphify"]
    assert find_command(lambda name: None) is None


def test_a_command_that_cannot_start(tmp_path: Path) -> None:
    with pytest.raises(GraphifyError, match="cannot start graphify"):
        tool.run([str(tmp_path / "missing")], ["--version"], cwd=None, timeout=5)


def test_graphify_runs_offline_without_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    script = "import os, json; print(json.dumps(dict(os.environ)))"
    env = json.loads(tool.run([sys.executable, "-c", script], [], cwd=None, timeout=30))
    assert env["GRAPHIFY_BACKEND"] == "none"
    assert "ANTHROPIC_API_KEY" not in env
    assert Graphify(("graphify",), "0.9.92").tested
    assert os.environ["ANTHROPIC_API_KEY"] == "sk-test"
