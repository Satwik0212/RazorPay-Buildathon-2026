import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.cart.requests import CartCreate, CartItemCreate, CartItemUpdate
from app.schemas.cart.responses import CartResponse, CartValidationResponse
from app.services.cart_service import CartService
from app.security.authentication import get_current_customer
from app.models.customer import Customer

router = APIRouter(prefix="/carts", tags=["Carts"])


@router.post("", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(
    req: CartCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    return service.create_or_get_cart(customer_id=current_customer.id, merchant_id=req.merchant_id)


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(
    cart_id: uuid.UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    return service.get_cart_for_customer(cart_id=cart_id, customer_id=current_customer.id)


@router.post("/{cart_id}/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    cart_id: uuid.UUID,
    req: CartItemCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    return service.add_item_to_cart(
        cart_id=cart_id,
        customer_id=current_customer.id,
        product_id=req.product_id,
        quantity=req.quantity,
    )


@router.patch("/{cart_id}/items/{item_id}", response_model=CartResponse)
def update_item_quantity(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    req: CartItemUpdate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    return service.update_item_quantity(
        cart_id=cart_id,
        customer_id=current_customer.id,
        item_id=item_id,
        quantity=req.quantity,
    )


@router.delete("/{cart_id}/items/{item_id}", response_model=CartResponse)
def remove_item(
    cart_id: uuid.UUID,
    item_id: uuid.UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    return service.remove_item_from_cart(
        cart_id=cart_id,
        customer_id=current_customer.id,
        item_id=item_id,
    )


@router.post("/{cart_id}/validate", response_model=CartValidationResponse)
def validate_cart(
    cart_id: uuid.UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = CartService(db)
    valid, issues = service.validate_cart(cart_id=cart_id, customer_id=current_customer.id)
    return CartValidationResponse(valid=valid, issues=issues)
