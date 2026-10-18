from pathlib import Path

import pytest

from spoolhq.core.config import ConfigError, ensure_home, home_dir, load_settings


def write_config(home: Path, text: str) -> Path:
    ensure_home()
    path = home / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_home_follows_env(home: Path) -> None:
    assert home_dir() == home


def test_defaults_without_config_file() -> None:
    settings = load_settings()
    assert (settings.host, settings.port, settings.log_level) == ("127.0.0.1", 8765, "INFO")


def test_config_file_is_read(home: Path) -> None:
    write_config(home, 'port = 9000\nlog_level = "debug"\n')
    settings = load_settings()
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"


def test_env_overrides_config_file(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config(home, "port = 9000\n")
    monkeypatch.setenv("SPOOLHQ_PORT", "9100")
    assert load_settings().port == 9100


def test_explicit_override_wins(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_config(home, "port = 9000\n")
    monkeypatch.setenv("SPOOLHQ_PORT", "9100")
    assert load_settings(port=9200).port == 9200


def test_invalid_config_names_field_and_file(home: Path) -> None:
    path = write_config(home, 'port = "not-a-port"\n')
    with pytest.raises(ConfigError) as excinfo:
        load_settings()
    message = str(excinfo.value)
    assert "'port'" in message
    assert str(path) in message


def test_unknown_key_is_named(home: Path) -> None:
    write_config(home, "prot = 9000\n")
    with pytest.raises(ConfigError, match="'prot'"):
        load_settings()


def test_malformed_toml_names_file(home: Path) -> None:
    path = write_config(home, "port = \n")
    with pytest.raises(ConfigError) as excinfo:
        load_settings()
    assert str(path) in str(excinfo.value)


def test_invalid_env_names_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPOOLHQ_PORT", "70000")
    with pytest.raises(ConfigError, match="'port'.*SPOOLHQ_PORT"):
        load_settings()


@pytest.mark.parametrize("source", ["env", "file"])
def test_non_loopback_host_is_refused(
    source: str, home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    all_interfaces = "0.0.0.0"  # noqa: S104 - the value under test, never bound
    if source == "env":
        monkeypatch.setenv("SPOOLHQ_HOST", all_interfaces)
    else:
        write_config(home, f'host = "{all_interfaces}"\n')
    with pytest.raises(ConfigError, match="'host'.*only listens on 127.0.0.1"):
        load_settings()
