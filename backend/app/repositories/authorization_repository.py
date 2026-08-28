import uuid
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.authorization import Authorization
from app.models.quote import Quote


class AuthorizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, authorization_id: uuid.UUID) -> Optional[Authorization]:
        stmt = (
            select(Authorization)
            .options(joinedload(Authorization.quote).joinedload(Quote.cart))
            .where(Authorization.id == authorization_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_by_quote_id(self, quote_id: uuid.UUID) -> Optional[Authorization]:
        stmt = select(Authorization).where(Authorization.quote_id == quote_id)
        return self.db.execute(stmt).scalars().first()

    def create(self, authorization: Authorization) -> Authorization:
        self.db.add(authorization)
        self.db.commit()
        self.db.refresh(authorization)
        return authorization

    def update_status(self, authorization_id: uuid.UUID, status: str) -> Optional[Authorization]:
        auth = self.get_by_id(authorization_id)
        if auth:
            auth.status = status
            self.db.commit()
            self.db.refresh(auth)
        return auth
