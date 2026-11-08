"""``GET /api/agents``: the same data as ``spool agents``."""

import pytest
from fastapi.testclient import TestClient

from spoolhq.api import create_app
from spoolhq.api.routers import agents as agents_router
from spoolhq.core.config import load_settings
from spoolhq.services.agents import BackendInfo
from spoolhq.services.codegraph import Graphify


class Detected:
    def detect(self) -> BackendInfo:
        return BackendInfo(
            name="claude-code-cli",
            installed=True,
            version="2.1.316",
            logged_in=True,
            auth_method="claude.ai",
            billing="subscription",
            policy_enforceable=True,
            reason=None,
        )


def test_agents_lists_backends_and_graphify(
    client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(agents_router, "available_runners", lambda: [Detected()])
    monkeypatch.setattr(agents_router, "probe", lambda: Graphify(("graphify",), "0.9.92"))
    body = client.get("/api/agents", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["backends"][0]["name"] == "claude-code-cli"
    assert body["backends"][0]["usable"] is True
    assert body["graphify"] == {"installed": True, "version": "0.9.92", "tested": True}

    monkeypatch.setattr(agents_router, "probe", lambda: None)
    body = client.get("/api/agents", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["graphify"] == {"installed": False, "version": None, "tested": False}
    assert body["fake_runner"] is None


def test_agents_reports_the_fake_runner(token: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agents_router, "available_runners", lambda: [])
    settings = load_settings()
    app = create_app(settings, token=token, fake_runner="happy")
    with TestClient(app, base_url=f"http://127.0.0.1:{settings.port}") as client:
        body = client.get("/api/agents", headers={"Authorization": f"Bearer {token}"}).json()
    assert body["fake_runner"] == "happy"


def test_agents_needs_the_token(client: TestClient) -> None:
    response = client.get("/api/agents")
    assert (response.status_code, response.json()["error"]["code"]) == (401, "unauthorized")
