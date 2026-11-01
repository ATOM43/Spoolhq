"""``GET /api/templates``: the built-in templates."""

from fastapi.testclient import TestClient

from spoolhq.services.templates import builtin_names


def test_list_templates(client: TestClient, token: str) -> None:
    response = client.get("/api/templates", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    listed = response.json()
    assert [template["name"] for template in listed] == builtin_names()
    assert "fastapi-react" in builtin_names()
    assert all(template["description"] for template in listed)


def test_list_templates_needs_the_token(client: TestClient) -> None:
    assert client.get("/api/templates").status_code == 401
