import uuid
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.security.authentication import get_current_customer
from app.models.customer import Customer
from app.services.upsell_service import UpsellService
from app.schemas.upsell.requests import UpsellSuggestionRequest
from app.schemas.upsell.responses import UpsellResponse

router = APIRouter(tags=["Buyer Upsell"])

@router.get("/buyer/products/{product_id}/suggestions", response_model=UpsellResponse)
def get_product_suggestions(
    product_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get upsell and cross-sell suggestions for a specific product.
    Used on the Product Detail Page before adding to cart.
    Unauthenticated (public endpoint).
    """
    service = UpsellService(db)
    return service.get_product_suggestions(product_id, limit=limit)

@router.post("/buyer/cart/{cart_id}/upsell-suggestions", response_model=UpsellResponse)
def get_cart_upsell_suggestions(
    cart_id: uuid.UUID,
    req: UpsellSuggestionRequest,
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    """
    Get upsell and cross-sell suggestions based on the current cart contents.
    Requires customer authentication.
    """
    service = UpsellService(db)
    return service.get_cart_suggestions(
        cart_id=cart_id, 
        customer_id=customer.id, 
        context=req.context, 
        limit=req.limit
    )
