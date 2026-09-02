import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.product.requests import (
    ProductCreate,
    ProductUpdate,
    ProductBulkCreate,
    InventoryUpdate,
)
from app.schemas.product.responses import (
    ProductResponse,
    ProductBulkResponse,
    InventoryResponse,
)
from app.core.exceptions import ForbiddenError
from app.schemas.common import PaginatedResponse
from app.services.product_service import ProductService
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.create_product(current_merchant.id, req)


@router.post("/bulk", response_model=ProductBulkResponse, status_code=status.HTTP_201_CREATED)
def bulk_create_products(
    req: ProductBulkCreate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.bulk_create_products(current_merchant.id, req)


@router.get("", response_model=PaginatedResponse[ProductResponse])
def list_products(
    category: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    items, total = service.list_products(
        merchant_id=current_merchant.id,
        category=category,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
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


@router.get("/categories", response_model=List[str])
def list_categories(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    return service.list_categories(current_merchant.id)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: uuid.UUID, 
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if product.merchant_id != current_merchant.id:
        raise ForbiddenError("You cannot access products of another merchant.")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    req: ProductUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.update_product(product_id, current_merchant.id, req)


@router.delete("/{product_id}", response_model=ProductResponse)
def delete_product(
    product_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.delete_product(product_id, current_merchant.id)


@router.patch("/{product_id}/reactivate", response_model=ProductResponse)
def reactivate_product(
    product_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.reactivate_product(product_id, current_merchant.id)


@router.get("/{product_id}/inventory", response_model=InventoryResponse)
def get_product_inventory(
    product_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if product.merchant_id != current_merchant.id:
        raise ForbiddenError("You cannot access inventory of another merchant.")
    return product.inventory


@router.patch("/{product_id}/inventory", response_model=InventoryResponse)
def update_product_inventory(
    product_id: uuid.UUID,
    req: InventoryUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    return service.update_inventory(product_id, current_merchant.id, req.available_quantity)
