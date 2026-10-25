from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base, get_session, make_engine
from app.main import create_app


@pytest.fixture
def engine(tmp_path: Path) -> Iterator[Engine]:
    """A fresh SQLite database with every table, per test."""
    engine = make_engine(f"sqlite:///{(tmp_path / 'test.db').as_posix()}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with sessionmaker(bind=engine, expire_on_commit=False)() as session:
        yield session


@pytest.fixture
def client(engine: Engine) -> Iterator[TestClient]:
    app = create_app()

    def test_session() -> Iterator[Session]:
        with sessionmaker(bind=engine, expire_on_commit=False)() as session:
            yield session

    app.dependency_overrides[get_session] = test_session
    with TestClient(app) as client:
        yield client
