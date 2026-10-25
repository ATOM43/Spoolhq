from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.core.db import make_engine

BACKEND = Path(__file__).resolve().parent.parent


def test_migrations_create_and_drop_the_schema(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'migrated.db').as_posix()}"
    config = Config(BACKEND / "alembic.ini")
    config.set_main_option("sqlalchemy.url", url)
    engine = make_engine(url)

    command.upgrade(config, "head")
    columns = {column["name"] for column in inspect(engine).get_columns("items")}
    assert columns == {"id", "name", "description"}

    command.downgrade(config, "base")
    assert "items" not in inspect(engine).get_table_names()
    engine.dispose()
