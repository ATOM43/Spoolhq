"""Response models of the GitHub endpoints."""

from pydantic import BaseModel


class GitHubSync(BaseModel):
    lines: list[str]
    """One line per open pull request: what was found and done."""
