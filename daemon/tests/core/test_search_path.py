"""core/search_path.py: folders appended to PATH for agent CLIs."""

import os
from pathlib import Path

from spoolhq.core.config import load_settings
from spoolhq.core.search_path import candidate_dirs, extended_path


def test_only_existing_folders_are_appended(tmp_path: Path) -> None:
    (tmp_path / ".local" / "bin").mkdir(parents=True)
    (tmp_path / ".cargo" / "bin").mkdir(parents=True)
    path = extended_path("/usr/bin", [], home=tmp_path, platform="linux", environ={})
    parts = path.split(os.pathsep)
    assert parts[0] == "/usr/bin"
    assert str(tmp_path / ".local" / "bin") in parts
    assert str(tmp_path / ".cargo" / "bin") in parts
    assert str(tmp_path / ".bun" / "bin") not in parts


def test_folders_already_on_path_are_never_duplicated(tmp_path: Path) -> None:
    local = tmp_path / ".local" / "bin"
    local.mkdir(parents=True)
    extra = tmp_path / "tools"
    extra.mkdir()
    current = os.pathsep.join(["/usr/bin", str(local) + os.sep])
    path = extended_path(current, [extra, extra], home=tmp_path, platform="linux", environ={})
    parts = path.split(os.pathsep)
    assert len([p for p in parts if Path(p) == local]) == 1
    assert parts.count(str(extra)) == 1
    assert extended_path(path, [extra], home=tmp_path, platform="linux", environ={}) == path


def test_extra_path_comes_last_and_must_exist(tmp_path: Path) -> None:
    extra = tmp_path / "my-bin"
    extra.mkdir()
    path = extended_path(
        "", [tmp_path / "missing", extra], home=tmp_path, platform="linux", environ={}
    )
    assert path.split(os.pathsep)[-1] == str(extra)
    assert str(tmp_path / "missing") not in path


def test_windows_adds_the_npm_folder_from_appdata(tmp_path: Path) -> None:
    dirs = candidate_dirs(tmp_path, "win32", {"APPDATA": str(tmp_path / "Roaming")})
    assert tmp_path / "Roaming" / "npm" in dirs
    assert Path("/opt/homebrew/bin") not in dirs
    assert Path("/opt/homebrew/bin") in candidate_dirs(tmp_path, "darwin", {})


def test_extra_path_is_read_from_config_toml(home: Path) -> None:
    home.mkdir()
    (home / "config.toml").write_text('extra_path = ["~/tools", "/opt/x/bin"]\n', "utf-8")
    settings = load_settings()
    assert settings.extra_path == [Path("~/tools").expanduser(), Path("/opt/x/bin")]
