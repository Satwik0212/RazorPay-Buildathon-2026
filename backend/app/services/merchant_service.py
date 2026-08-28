import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.merchant import Merchant
from app.repositories.merchant_repository import MerchantRepository
from app.schemas.merchant.requests import MerchantCreate, MerchantUpdate
from app.core.exceptions import NotFoundError
from app.core.constants import ActorType, AuditEventType
from app.services.audit_service import AuditService


class MerchantService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = MerchantRepository(db)
        self.audit_service = AuditService(db)

    def get_merchant_by_id(self, merchant_id: uuid.UUID) -> Merchant:
        merchant = self.repo.get_merchant_by_id(merchant_id)
        if not merchant:
            raise NotFoundError("Merchant", merchant_id)
        return merchant

    def get_merchant_by_user_id(self, user_id: uuid.UUID) -> Merchant:
        merchant = self.repo.get_merchant_by_user_id(user_id)
        if not merchant:
            raise NotFoundError("Merchant Profile for User", user_id)
        return merchant

    def update_merchant_profile(self, merchant: Merchant, req: MerchantUpdate) -> Merchant:
        if req.name is not None:
            merchant.name = req.name
        if req.description is not None:
            merchant.description = req.description
        if req.is_active is not None:
            merchant.is_active = req.is_active

        updated = self.repo.update_merchant(merchant)

        self.audit_service.log_event(
            event_type=AuditEventType.MERCHANT_UPDATED.value,
            actor_type=ActorType.MERCHANT.value,
            entity_type="merchant",
            actor_id=merchant.user_id,
            merchant_id=merchant.id,
            entity_id=merchant.id,
            event_data={"name": merchant.name, "is_active": merchant.is_active},
        )
        return updated

    def list_merchants(self, limit: int = 50, offset: int = 0) -> List[Merchant]:
        return self.repo.list_merchants(limit=limit, offset=offset)
