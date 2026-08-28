import uuid
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.quote import Quote


class QuoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, quote_id: uuid.UUID) -> Optional[Quote]:
        stmt = (
            select(Quote)
            .options(joinedload(Quote.cart))
            .where(Quote.id == quote_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_latest_quote_for_cart(self, cart_id: uuid.UUID) -> Optional[Quote]:
        stmt = (
            select(Quote)
            .where(Quote.cart_id == cart_id)
            .order_by(Quote.created_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def create(self, quote: Quote) -> Quote:
        self.db.add(quote)
        self.db.commit()
        self.db.refresh(quote)
        return quote
