import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.product.requests import ProductCreate
from app.schemas.product.responses import ProductResponse
from app.schemas.common import PaginatedResponse
from app.services.product_service import ProductService
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(prefix="/catalog", tags=["Catalog"])


@router.get("", response_model=PaginatedResponse[ProductResponse])
def get_catalog(
    merchant_id: Optional[uuid.UUID] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    items, total = service.list_products(
        merchant_id=merchant_id,
        category=category,
        is_active=True,
        search=search,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse(
        items=[ProductResponse.model_validate(p) for p in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_catalog_product(
    req: ProductCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.create_product(current_merchant.id, req)
