"""``GET /api/templates``: the built-in project templates (token required)."""

from fastapi import APIRouter, Security

from spoolhq.api.schemas.templates import TemplateView
from spoolhq.api.security import bearer_scheme
from spoolhq.services.templates import builtin_contracts

router = APIRouter(prefix="/api/templates", dependencies=[Security(bearer_scheme)])


@router.get("")
def list_templates() -> list[TemplateView]:
    return [
        TemplateView(name=name, description=contract.description, summary=contract.summary)
        for name, contract in builtin_contracts()
    ]
