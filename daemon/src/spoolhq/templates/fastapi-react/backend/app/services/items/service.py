"""Creating and reading items."""

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.services.items.models import Item


def create_item(session: Session, *, name: str, description: str = "") -> Item:
    item = Item(name=name, description=description)
    session.add(item)
    session.commit()
    return item


def list_items(session: Session) -> Sequence[Item]:
    return session.scalars(select(Item).order_by(Item.id)).all()


def get_item(session: Session, item_id: int) -> Item | None:
    return session.get(Item, item_id)
