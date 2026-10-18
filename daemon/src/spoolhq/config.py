"""Home folder and settings.

Settings come from ``<home>/config.toml`` and then from ``SPOOLHQ_*`` environment
variables, which win. The home folder is ``~/.spoolhq`` unless ``SPOOLHQ_HOME`` is set.
"""

import os
import sys
import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

HOME_ENV_VAR = "SPOOLHQ_HOME"
ENV_PREFIX = "SPOOLHQ_"
LOOPBACK_HOST = "127.0.0.1"

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class ConfigError(Exception):
    """The configuration is invalid; the message says which field and where it came from."""


def home_dir() -> Path:
    """Return the SpoolHQ home folder (not created)."""
    override = os.environ.get(HOME_ENV_VAR)
    return Path(override) if override else Path.home() / ".spoolhq"


def config_path() -> Path:
    return home_dir() / "config.toml"


def ensure_home() -> Path:
    """Create the home folder with mode 0700 if it does not exist, and return it."""
    home = home_dir()
    try:
        home.mkdir(mode=0o700, parents=True)
    except FileExistsError:
        return home
    if sys.platform != "win32":
        # mkdir's mode is filtered by the umask; set it exactly.
        home.chmod(0o700)
    return home


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX, extra="forbid")

    host: str = LOOPBACK_HOST
    port: int = Field(default=8765, ge=1, le=65535)
    log_level: LogLevel = "INFO"

    @field_validator("host")
    @classmethod
    def _loopback_only(cls, value: str) -> str:
        if value != LOOPBACK_HOST:
            raise ValueError(
                f"SpoolHQ only listens on {LOOPBACK_HOST}; refusing to bind to {value!r}"
            )
        return value

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper_log_level(cls, value: Any) -> Any:
        return value.upper() if isinstance(value, str) else value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # Earlier sources win: explicit arguments (CLI flags), then env, then config.toml.
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, toml_file=config_path()),
        )


def load_settings(**overrides: Any) -> Settings:
    """Load settings, raising ConfigError with the field name and its source on failure."""
    path = config_path()
    try:
        return Settings(**overrides)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"invalid config file {path}: {exc}") from exc
    except ValidationError as exc:
        env_names = {name.upper() for name in os.environ}
        problems = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            env_name = f"{ENV_PREFIX}{field.upper()}"
            if field in overrides:
                source = "command-line option"
            elif env_name in env_names:
                source = f"environment variable {env_name}"
            else:
                source = str(path)
            problems.append(f"invalid setting '{field}' ({source}): {error['msg']}")
        raise ConfigError("\n".join(problems)) from exc
