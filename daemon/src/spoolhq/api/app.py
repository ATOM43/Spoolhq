"""The daemon's FastAPI application."""

from fastapi import APIRouter, FastAPI, Security
from fastapi.security import HTTPBearer

import spoolhq
from spoolhq.api.security import LocalOnlyMiddleware
from spoolhq.auth import load_or_create_token
from spoolhq.config import Settings, ensure_home

# LocalOnlyMiddleware enforces the token; this only documents it in /docs, where the
# Authorize button then works.
_bearer = HTTPBearer(auto_error=False, description="The token in ~/.spoolhq/token")

public = APIRouter(prefix="/api")
protected = APIRouter(prefix="/api", dependencies=[Security(_bearer)])


@public.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@protected.get("/version")
def version() -> dict[str, str]:
    return {"version": spoolhq.__version__}


def create_app(settings: Settings, *, token: str | None = None) -> FastAPI:
    """Build the app. Without ``token``, the one in the home folder is used (or created)."""
    if token is None:
        token = load_or_create_token(ensure_home())
    app = FastAPI(title="SpoolHQ daemon", version=spoolhq.__version__)
    app.include_router(public)
    app.include_router(protected)
    app.add_middleware(LocalOnlyMiddleware, port=settings.port, token=token)
    return app
