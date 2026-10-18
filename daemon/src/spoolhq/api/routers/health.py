"""``GET /api/health``: public, so clients can detect a running daemon."""

from fastapi import APIRouter

from spoolhq.api.schemas.health import Health

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> Health:
    return Health()
