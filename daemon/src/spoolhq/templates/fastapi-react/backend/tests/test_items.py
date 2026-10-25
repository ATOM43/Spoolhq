from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import items


def test_create_and_get(client: TestClient) -> None:
    created = client.post("/api/items", json={"name": "Spool", "description": "red"})
    assert created.status_code == 201
    body = created.json()
    assert body == {"id": body["id"], "name": "Spool", "description": "red"}

    fetched = client.get(f"/api/items/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_list_in_creation_order(client: TestClient) -> None:
    for name in ("first", "second"):
        client.post("/api/items", json={"name": name})
    response = client.get("/api/items")
    assert response.status_code == 200
    assert [item["name"] for item in response.json()] == ["first", "second"]


def test_get_missing_item_is_404(client: TestClient) -> None:
    response = client.get("/api/items/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "item not found"}


def test_create_rejects_an_empty_name(client: TestClient) -> None:
    assert client.post("/api/items", json={"name": ""}).status_code == 422


def test_service_without_http(session: Session) -> None:
    item = items.create_item(session, name="direct")
    assert items.get_item(session, item.id) == item
    assert list(items.list_items(session)) == [item]
    assert items.get_item(session, item.id + 1) is None
