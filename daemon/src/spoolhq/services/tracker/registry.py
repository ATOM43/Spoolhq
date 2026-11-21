"""Tracker adapters by ``tracker.kind``. Adding one: write the adapter, add it here and to
``Tracker.kind`` in ``services/projects/model.py``, and pass the contract suite
(docs/tracker.md#writing-an-adapter)."""

from collections.abc import Callable

import httpx

from spoolhq.services.projects.model import Tracker
from spoolhq.services.tracker.base import TrackerAdapter
from spoolhq.services.tracker.clickup import ClickUpAdapter

AdapterFactory = Callable[[Tracker, str, httpx.BaseTransport | None], TrackerAdapter]

ADAPTERS: dict[str, AdapterFactory] = {
    "clickup": lambda settings, token, transport: ClickUpAdapter(
        settings.list_id, settings.status_map, token, transport=transport
    ),
}


def make_adapter(
    settings: Tracker, token: str, transport: httpx.BaseTransport | None = None
) -> TrackerAdapter:
    return ADAPTERS[settings.kind](settings, token, transport)
