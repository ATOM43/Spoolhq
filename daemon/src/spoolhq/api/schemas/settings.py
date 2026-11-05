"""Response models of the daemon settings and secrets endpoints."""

from pydantic import BaseModel, Field

from spoolhq.services.secrets import SecretSource


class SecretView(BaseModel):
    """Whether a secret is set and where; never its value."""

    set: bool
    source: SecretSource | None


class DaemonSettings(BaseModel):
    host: str
    port: int
    log_level: str
    projects_dir: str
    worktrees_dir: str
    allowed_origins: list[str]
    secrets: dict[str, SecretView]
    """``anthropic``, ``github`` and ``clickup``."""


class SecretValue(BaseModel):
    value: str = Field(min_length=1, max_length=10_000)


class SecretTest(BaseModel):
    """The outcome of testing a secret against its provider, in fixed words only."""

    ok: bool
    message: str
