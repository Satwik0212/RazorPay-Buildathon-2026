import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.policy import Policy


class PolicyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_merchant_id(self, merchant_id: uuid.UUID) -> Optional[Policy]:
        stmt = select(Policy).where(Policy.merchant_id == merchant_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create_or_update(self, policy_data: dict, merchant_id: uuid.UUID) -> Policy:
        policy = self.get_by_merchant_id(merchant_id)
        if not policy:
            policy = Policy(merchant_id=merchant_id, **policy_data)
            self.db.add(policy)
        else:
            for k, v in policy_data.items():
                setattr(policy, k, v)
        self.db.commit()
        self.db.refresh(policy)
        return policy
