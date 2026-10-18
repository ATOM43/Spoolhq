"""The daemon's FastAPI application."""

from fastapi import FastAPI

import spoolhq
from spoolhq.api.routers import health, version
from spoolhq.api.security import LocalOnlyMiddleware
from spoolhq.core.auth import load_or_create_token
from spoolhq.core.config import Settings, ensure_home


def create_app(settings: Settings, *, token: str | None = None) -> FastAPI:
    """Build the app. Without ``token``, the one in the home folder is used (or created)."""
    if token is None:
        token = load_or_create_token(ensure_home())
    app = FastAPI(title="SpoolHQ daemon", version=spoolhq.__version__)
    app.include_router(health.router)
    app.include_router(version.router)
    app.add_middleware(LocalOnlyMiddleware, port=settings.port, token=token)
    return app
