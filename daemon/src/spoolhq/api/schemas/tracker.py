"""Response models of the tracker endpoints."""

from typing import Literal

from pydantic import BaseModel


class TrackerView(BaseModel):
    kind: str | None
    """``tracker.kind`` from ``project.yaml``; null without a ``tracker`` block."""
    state: Literal["off", "ok", "syncing", "failed"]
    """``off``: no tracker block; ``failed``: an action failed 5 times and nothing has
    succeeded since; ``syncing``: actions are waiting; ``ok``: nothing waiting."""
    pending: int
    last_error: str | None
    """A fixed message built by SpoolHQ, never a tracker's response body or the token."""
    last_synced_at: str | None
    failed_at: str | None
    """When the sync last went ``failed``; null unless ``state`` is ``failed``."""


class TrackerPush(BaseModel):
    queued: int
    """How many actions were queued (a ticket with a push already waiting adds none)."""
