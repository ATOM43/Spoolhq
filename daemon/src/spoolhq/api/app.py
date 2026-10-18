"""The daemon's FastAPI application."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI

import spoolhq
from spoolhq.api.routers import health, version
from spoolhq.api.security import LocalOnlyMiddleware
from spoolhq.api.worktrees import check_git, recover_all_worktrees
from spoolhq.core.auth import load_or_create_token
from spoolhq.core.config import Settings, ensure_home
from spoolhq.services.runs import RunRegistry

logger = logging.getLogger("spoolhq.daemon")


def create_app(
    settings: Settings, *, token: str | None = None, daemon_instance: str | None = None
) -> FastAPI:
    """Build the app. Without ``token``, the one in the home folder is used (or created).

    On startup the app opens every workspace's run log and recovers the runs a previous
    daemon left active (``app.state.runs``), under a fresh ``daemon_instance`` unless
    one is given; then it checks git and removes the worktrees those runs left behind
    (``app.state.worktree_recovery``). The caller must hold the daemon single-instance
    lock while it runs.
    """
    if token is None:
        token = load_or_create_token(ensure_home())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        instance = daemon_instance or uuid4().hex
        registry = RunRegistry.start(settings.projects_dir, daemon_instance=instance)
        logger.info(
            "run logs open",
            extra={"daemon_instance": instance, "projects": registry.projects},
        )
        app.state.daemon_instance = instance
        app.state.runs = registry
        try:
            check_git()
            app.state.worktree_recovery = recover_all_worktrees(
                settings.projects_dir, settings.worktrees_dir, registry
            )
            yield
        finally:
            registry.close()

    app = FastAPI(title="SpoolHQ daemon", version=spoolhq.__version__, lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(version.router)
    app.add_middleware(LocalOnlyMiddleware, port=settings.port, token=token)
    return app
