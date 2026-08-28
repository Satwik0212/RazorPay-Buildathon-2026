import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.audit.responses import AuditEventResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService
from app.security.authentication import get_current_merchant, get_current_user
from app.models.merchant import Merchant, User
from app.core.exceptions import ForbiddenError
from app.core.constants import UserRole

router = APIRouter(tags=["Audit"])


@router.get("/audit", response_model=PaginatedResponse[AuditEventResponse])
def list_system_audit_events(
    merchant_id: Optional[uuid.UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.ADMIN.value:
        raise ForbiddenError("Only administrators can view system audit logs.")
        
    service = AuditService(db)
    events, total = service.list_events(
        merchant_id=merchant_id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/merchant/audit", response_model=PaginatedResponse[AuditEventResponse])
def list_merchant_audit_events(
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    event_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = AuditService(db)
    events, total = service.list_events(
        merchant_id=current_merchant.id,
        entity_type=entity_type,
        entity_id=entity_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )
