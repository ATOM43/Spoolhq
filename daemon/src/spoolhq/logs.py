"""Structured logging: JSON lines to a rotating file, plain text to stderr when interactive."""

import json
import logging
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

LOG_FILE_NAME = "daemon.log"
MAX_BYTES = 10 * 1024 * 1024
BACKUP_COUNT = 5
REDACTED = "[redacted]"

# Attributes every LogRecord has; anything else on a record came from `extra=`.
_RECORD_ATTRS = frozenset(vars(logging.LogRecord("", 0, "", 0, "", None, None))) | {
    "message",
    "asctime",
    "color_message",  # uvicorn's coloured duplicate of msg
}

# Marks the handlers configure_logging installs, so a second call replaces only them.
_HANDLER_FLAG = "_spoolhq_handler"


class _Redactor:
    def __init__(self, secrets: Iterable[str]) -> None:
        self._secrets = [secret for secret in secrets if secret]

    def __call__(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, REDACTED)
        return text


class JsonFormatter(logging.Formatter):
    """One JSON object per line: ts, level, logger, msg, then any extras."""

    def __init__(self, redact: Iterable[str] = ()) -> None:
        super().__init__()
        self._redact = _Redactor(redact)

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in vars(record).items():
            if key not in _RECORD_ATTRS and key not in entry:
                entry[key] = value
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return self._redact(json.dumps(entry, default=str, ensure_ascii=False))


class PlainFormatter(logging.Formatter):
    def __init__(self, redact: Iterable[str] = ()) -> None:
        super().__init__("%(asctime)s %(levelname)-8s %(name)s: %(message)s")
        self._redact = _Redactor(redact)

    def format(self, record: logging.LogRecord) -> str:
        return self._redact(super().format(record))


def configure_logging(
    log_dir: Path,
    level: str = "INFO",
    *,
    redact: Iterable[str] = (),
    interactive: bool | None = None,
) -> Path:
    """Send all logs (uvicorn's included) to ``log_dir/daemon.log``; return its path.

    Strings in ``redact`` (the auth token) are replaced before anything is written.
    """
    redact = list(redact)
    if interactive is None:
        interactive = sys.stderr.isatty()
    log_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    log_file = log_dir / LOG_FILE_NAME

    root = logging.getLogger()
    for handler in [h for h in root.handlers if getattr(h, _HANDLER_FLAG, False)]:
        root.removeHandler(handler)
        handler.close()

    file_handler = RotatingFileHandler(
        log_file, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    file_handler.setFormatter(JsonFormatter(redact))
    handlers: list[logging.Handler] = [file_handler]
    if interactive:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(PlainFormatter(redact))
        handlers.append(stderr_handler)
    for handler in handlers:
        setattr(handler, _HANDLER_FLAG, True)
        root.addHandler(handler)
    root.setLevel(level)

    # uvicorn installs no handlers of its own when run with log_config=None; make sure
    # its loggers reach ours.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
    return log_file
