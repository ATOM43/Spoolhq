"""Response model of the template list."""

from pydantic import BaseModel


class TemplateView(BaseModel):
    name: str
    """What ``POST /api/projects`` takes as ``template``."""
    description: str
    summary: str | None = None
    """One line of at most 120 characters, for a template card."""
