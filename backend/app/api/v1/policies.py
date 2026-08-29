from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.policy.requests import PolicyUpdate, PolicyCheckRequest
from app.schemas.policy.responses import PolicyResponse, PolicyCheckResponse
from app.services.policy_service import PolicyService
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(prefix="/merchant/policy", tags=["Policies"])


@router.get("", response_model=PolicyResponse)
def get_policy(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = PolicyService(db)
    return service.get_merchant_policy(current_merchant.id)


@router.put("", response_model=PolicyResponse)
def update_policy(
    req: PolicyUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = PolicyService(db)
    return service.update_merchant_policy(current_merchant.id, req)


@router.post("/check", response_model=PolicyCheckResponse)
def check_policy(
    req: PolicyCheckRequest,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    service = PolicyService(db)
    status, reason = service.evaluate_transaction(
        merchant_id=current_merchant.id,
        amount=req.amount,
        categories=[req.category] if req.category else [],
        is_ai_agent=True,
    )
    return PolicyCheckResponse(
        allowed=(status.value == "APPROVED"),
        status=status.value,
        reason=reason,
    )
