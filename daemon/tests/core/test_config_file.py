"""Setting one value in config.toml: other lines kept, unsafe files refused."""

from pathlib import Path

import pytest

from spoolhq.core.config import ConfigError, load_settings
from spoolhq.core.config_file import set_bool


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("", "[desktop]\nkeep_running = false\n"),
        ("port = 9000", "port = 9000\n\n[desktop]\nkeep_running = false\n"),
        (
            "[desktop]\nkeep_running = true  # on\n\n[other]\nkeep_running = true\n",
            "[desktop]\nkeep_running = false\n\n[other]\nkeep_running = true\n",
        ),
        ("[desktop]\n# later\n", "[desktop]\nkeep_running = false\n# later\n"),
    ],
)
def test_set_bool_edits_only_its_line(tmp_path: Path, before: str, after: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(before, encoding="utf-8")
    set_bool(path, "desktop", "keep_running", False)
    assert path.read_bytes().decode("utf-8") == after


def test_set_bool_creates_the_file(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    set_bool(path, "desktop", "keep_running", True)
    assert path.read_text(encoding="utf-8") == "[desktop]\nkeep_running = true\n"


@pytest.mark.parametrize(
    "text", ["desktop = { keep_running = true }\n", "port = \n", "[desktop]\nkeep_running.x = 1\n"]
)
def test_set_bool_refuses_what_it_cannot_edit(tmp_path: Path, text: str) -> None:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ConfigError, match=r"cannot set desktop\.keep_running"):
        set_bool(path, "desktop", "keep_running", False)
    assert path.read_text(encoding="utf-8") == text


def test_the_desktop_table_loads(home: Path) -> None:
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.toml").write_text("[desktop]\nkeep_running = false\n", encoding="utf-8")
    assert load_settings().desktop.keep_running is False
    (home / "config.toml").write_text("", encoding="utf-8")
    assert load_settings().desktop.keep_running is True
    (home / "config.toml").write_text("[desktop]\nunknown = 1\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="desktop.unknown"):
        load_settings()
