"""Response model of the template list."""

from pydantic import BaseModel


class TemplateView(BaseModel):
    name: str
    """What ``POST /api/projects`` takes as ``template``."""
    description: str
