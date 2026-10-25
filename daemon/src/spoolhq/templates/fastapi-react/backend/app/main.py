"""The FastAPI application."""

from fastapi import FastAPI

from app.api.routers import health, items


def create_app() -> FastAPI:
    app = FastAPI(title="API")
    app.include_router(health.router, prefix="/api")
    app.include_router(items.router, prefix="/api")
    return app


app = create_app()
