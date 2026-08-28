import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.merchant import User, Merchant


class MerchantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.get(User, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_merchant_by_id(self, merchant_id: uuid.UUID) -> Optional[Merchant]:
        return self.db.get(Merchant, merchant_id)

    def get_merchant_by_user_id(self, user_id: uuid.UUID) -> Optional[Merchant]:
        stmt = select(Merchant).where(Merchant.user_id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_merchant(self, merchant: Merchant) -> Merchant:
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant

    def update_merchant(self, merchant: Merchant) -> Merchant:
        self.db.commit()
        self.db.refresh(merchant)
        return merchant

    def list_merchants(self, limit: int = 50, offset: int = 0) -> List[Merchant]:
        stmt = select(Merchant).where(Merchant.is_active == True).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars().all())
