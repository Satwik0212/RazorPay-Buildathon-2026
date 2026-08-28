import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.merchant.requests import MerchantUpdate
from app.schemas.merchant.responses import MerchantResponse
from app.services.merchant_service import MerchantService
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("/me", response_model=MerchantResponse)
def get_current_merchant_profile(current_merchant: Merchant = Depends(get_current_merchant)):
    return current_merchant


@router.patch("/me", response_model=MerchantResponse)
def update_current_merchant_profile(
    req: MerchantUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = MerchantService(db)
    return service.update_merchant_profile(current_merchant, req)


@router.get("", response_model=List[MerchantResponse])
def list_merchants(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = MerchantService(db)
    return service.list_merchants(limit=limit, offset=offset)


@router.get("/{merchant_id}", response_model=MerchantResponse)
def get_merchant_by_id(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    service = MerchantService(db)
    return service.get_merchant_by_id(merchant_id)
