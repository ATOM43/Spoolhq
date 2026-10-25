from pathlib import Path

import pytest
from sqlalchemy import inspect

from app.core import db
from app.core.config import Settings, get_settings


def test_settings_read_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///other.db")
    assert Settings().database_url == "sqlite:///other.db"


def test_default_session_uses_the_configured_database(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_DATABASE_URL", f"sqlite:///{(tmp_path / 'app.db').as_posix()}")
    get_settings.cache_clear()
    db.get_engine.cache_clear()
    try:
        session = next(db.get_session())
        db.Base.metadata.create_all(session.get_bind())
        assert "items" in inspect(session.get_bind()).get_table_names()
        session.close()
    finally:
        get_settings.cache_clear()
        db.get_engine.cache_clear()
