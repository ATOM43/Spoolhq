"""Alembic's entry point: migrates ``Base.metadata`` on the configured database."""

from alembic import context
from sqlalchemy import Connection

import app.services.items  # noqa: F401  (registers the models on Base.metadata)
from app.core.config import get_settings
from app.core.db import Base, make_engine

target_metadata = Base.metadata


def url() -> str:
    configured = context.config.get_main_option("sqlalchemy.url")
    return configured or get_settings().database_url


def run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    with make_engine(url()).connect() as connection:
        run(connection)
