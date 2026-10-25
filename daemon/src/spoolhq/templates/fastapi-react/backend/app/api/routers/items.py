"""``/api/items``: create, list and get items."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import SessionDep
from app.api.schemas.items import ItemCreate, ItemRead
from app.services import items

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_item(body: ItemCreate, session: SessionDep) -> ItemRead:
    item = items.create_item(session, name=body.name, description=body.description)
    return ItemRead.model_validate(item)


@router.get("")
def list_items(session: SessionDep) -> list[ItemRead]:
    return [ItemRead.model_validate(item) for item in items.list_items(session)]


@router.get("/{item_id}")
def get_item(item_id: int, session: SessionDep) -> ItemRead:
    item = items.get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")
    return ItemRead.model_validate(item)
