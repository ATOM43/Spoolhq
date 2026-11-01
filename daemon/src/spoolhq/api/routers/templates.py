"""``GET /api/templates``: the built-in project templates (token required)."""

from fastapi import APIRouter, Security

from spoolhq.api.schemas.templates import TemplateView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.templates import builtin_descriptions

router = APIRouter(prefix="/api/templates", dependencies=[Security(bearer_scheme)])


@router.get("")
def list_templates() -> list[TemplateView]:
    return [
        TemplateView(name=name, description=description)
        for name, description in builtin_descriptions()
    ]
