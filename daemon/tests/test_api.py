from pathlib import Path

from fastapi.testclient import TestClient

import spoolhq
from spoolhq.api import create_app
from spoolhq.auth import read_token
from spoolhq.config import load_settings


def test_health_needs_no_token(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version_without_token_is_401(client: TestClient) -> None:
    response = client.get("/api/version")
    assert response.status_code == 401
    assert response.json() == {"detail": "missing or invalid token"}


def test_version_with_wrong_token_is_401(client: TestClient, token: str) -> None:
    response = client.get("/api/version", headers={"Authorization": "Bearer not-the-token"})
    assert response.status_code == 401
    assert token not in response.text


def test_version_with_token_is_200(client: TestClient, token: str) -> None:
    response = client.get("/api/version", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"version": spoolhq.__version__}


def test_unknown_api_route_needs_token(client: TestClient) -> None:
    assert client.get("/api/does-not-exist").status_code == 401


def test_foreign_host_header_is_rejected(client: TestClient, token: str) -> None:
    headers = {"Host": "evil.example", "Authorization": f"Bearer {token}"}
    for path in ("/api/health", "/api/version", "/docs"):
        response = client.get(path, headers=headers)
        assert response.status_code == 400
        assert response.json() == {"detail": "invalid Host header"}


def test_host_header_must_match_port(client: TestClient) -> None:
    assert client.get("/api/health", headers={"Host": "localhost:8765"}).status_code == 200
    assert client.get("/api/health", headers={"Host": "localhost:1234"}).status_code == 400
    assert client.get("/api/health", headers={"Host": "127.0.0.1"}).status_code == 400


def test_docs_and_openapi_are_served(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_create_app_uses_token_file(home: Path) -> None:
    app = create_app(load_settings())
    token = read_token(home)
    assert token is not None
    with TestClient(app, base_url="http://127.0.0.1:8765") as test_client:
        response = test_client.get("/api/version", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
