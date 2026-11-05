"""Response model of the template list."""

from pydantic import BaseModel


class TemplateCommandsView(BaseModel):
    install: str
    lint: str
    test: str


class TemplateView(BaseModel):
    name: str
    """What ``POST /api/projects`` takes as ``template``."""
    description: str
    summary: str | None = None
    """One line of at most 120 characters, for a template card."""
    commands: TemplateCommandsView
    """The stack commands the template declares; the app's dialog pre-fills them."""
