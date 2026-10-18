import json
import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.config import load_settings
from spoolhq.logs import REDACTED, configure_logging


@pytest.fixture
def log_file(home: Path, token: str) -> Iterator[Path]:
    path = configure_logging(home / "logs", "DEBUG", redact=[token], interactive=False)
    yield path
    # Close our handlers so the temp dir can be removed (Windows keeps open files locked).
    root = logging.getLogger()
    for handler in [h for h in root.handlers if getattr(h, "_spoolhq_handler", False)]:
        root.removeHandler(handler)
        handler.close()
    root.setLevel(logging.WARNING)


def read_lines(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_log_lines_are_json_without_token(log_file: Path, token: str) -> None:
    app = create_app(load_settings(), token=token)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        client.get("/api/version", headers={"Authorization": f"Bearer {token}"})
        client.get("/api/version", headers={"Authorization": "Bearer wrong"})
    logger = logging.getLogger("spoolhq.test")
    logger.info("something happened", extra={"ticket": "T02"})
    logger.warning("careless message with %s", token)

    text = log_file.read_text(encoding="utf-8")
    assert token not in text
    entries = read_lines(log_file)
    assert entries
    for entry in entries:
        assert {"ts", "level", "logger", "msg"} <= entry.keys()
        assert str(entry["ts"]).endswith("+00:00")
    assert {"logger": "spoolhq.test", "msg": "something happened", "ticket": "T02"}.items() <= (
        entries[-2].items()
    )
    assert entries[-1]["msg"] == f"careless message with {REDACTED}"
    assert any(entry["msg"] == "rejected unauthenticated request" for entry in entries)


def test_exceptions_are_logged(log_file: Path) -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        logging.getLogger("spoolhq.test").exception("failed")
    entry = read_lines(log_file)[-1]
    assert entry["level"] == "ERROR"
    assert "ValueError: boom" in str(entry["exc"])


def test_reconfiguring_replaces_handlers(home: Path, log_file: Path) -> None:
    configure_logging(home / "logs", "INFO", interactive=False)
    ours = [h for h in logging.getLogger().handlers if getattr(h, "_spoolhq_handler", False)]
    assert len(ours) == 1
