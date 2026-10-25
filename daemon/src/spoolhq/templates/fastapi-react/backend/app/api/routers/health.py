"""``GET /api/health``."""

from fastapi import APIRouter

from app.api.schemas.health import Health

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> Health:
    return Health(status="ok")
