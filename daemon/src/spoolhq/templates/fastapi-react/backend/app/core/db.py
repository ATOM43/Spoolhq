"""The SQLAlchemy engine, sessions and the declarative base every model uses."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class of every model; its metadata is what Alembic migrates."""


def make_engine(url: str) -> Engine:
    # SQLite connections are used from FastAPI's worker threads.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


@lru_cache
def get_engine() -> Engine:
    return make_engine(get_settings().database_url)


def get_session() -> Iterator[Session]:
    """One session per request (or unit of work), closed afterwards."""
    with sessionmaker(bind=get_engine(), expire_on_commit=False)() as session:
        yield session
