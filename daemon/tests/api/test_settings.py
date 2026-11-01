"""Daemon settings and write-only secrets (an in-memory keychain from the autouse
``keychain`` fixture)."""

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.conftest import MemoryKeyring

SECRET = "sk-test-0123456789-do-not-leak"  # noqa: S105 - a fake value the test looks for


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_settings_show_where_secrets_come_from(
    client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPOOLHQ_GITHUB_TOKEN", "from-env")
    body = client.get("/api/settings", headers=auth(token)).json()
    assert body["host"] == "127.0.0.1"
    assert "tauri://localhost" in body["allowed_origins"]
    assert body["secrets"] == {
        "anthropic": {"set": False, "source": None},
        "github": {"set": True, "source": "env"},
        "clickup": {"set": False, "source": None},
    }
    assert "from-env" not in str(body)


def test_a_secret_is_stored_and_never_echoed(
    client: TestClient,
    token: str,
    keychain: MemoryKeyring,
    home: Path,
    projects_dir: Path,
    workspace: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    responses = [
        client.put("/api/settings/secrets/clickup", json={"value": SECRET}, headers=auth(token)),
        client.get("/api/settings", headers=auth(token)),
    ]
    assert responses[0].status_code == 204
    assert responses[1].json()["secrets"]["clickup"] == {"set": True, "source": "keychain"}
    assert keychain.get_password("spoolhq", "clickup") == SECRET

    responses.append(client.delete("/api/settings/secrets/clickup", headers=auth(token)))
    assert responses[-1].status_code == 204
    assert keychain.get_password("spoolhq", "clickup") is None
    responses.append(client.delete("/api/settings/secrets/clickup", headers=auth(token)))
    assert responses[-1].status_code == 204

    assert all(SECRET not in r.text for r in responses)
    assert SECRET not in caplog.text
    for folder in (home, projects_dir):
        for path in folder.rglob("*"):
            if path.is_file():
                assert SECRET.encode() not in path.read_bytes(), path


def test_secret_refusals(client: TestClient, token: str) -> None:
    unknown = client.put("/api/settings/secrets/aws", json={"value": "x"}, headers=auth(token))
    assert (unknown.status_code, unknown.json()["error"]["field"]) == (422, "secret")
    empty = client.put("/api/settings/secrets/github", json={"value": ""}, headers=auth(token))
    assert empty.status_code == 422
    assert "value" not in empty.json()["error"]["message"].split(":", 1)[1]
    blank = client.put("/api/settings/secrets/github", json={"value": "  "}, headers=auth(token))
    assert (blank.status_code, blank.json()["error"]["field"]) == (422, "value")


def test_no_keychain_is_a_readable_error(
    client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from keyring.errors import NoKeyringError

    def broken(*_args: object) -> None:
        raise NoKeyringError(SECRET)

    monkeypatch.setattr("keyring.set_password", broken)
    monkeypatch.setattr("keyring.delete_password", broken)
    put = client.put("/api/settings/secrets/github", json={"value": SECRET}, headers=auth(token))
    assert (put.status_code, put.json()["error"]["code"]) == (409, "keychain_unavailable")
    assert SECRET not in put.text
    delete = client.delete("/api/settings/secrets/github", headers=auth(token))
    assert delete.status_code == 409
