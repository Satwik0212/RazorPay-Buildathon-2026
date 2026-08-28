import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.quote.requests import QuoteCreate
from app.schemas.quote.responses import QuoteResponse, QuoteValidationResponse
from app.services.quote_service import QuoteService
from app.security.authentication import get_current_customer
from app.models.customer import Customer

router = APIRouter(prefix="/quotes", tags=["Quotes"])


@router.post("", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(
    req: QuoteCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = QuoteService(db)
    quote = service.create_quote(cart_id=req.cart_id, customer_id=current_customer.id)
    return QuoteResponse(
        quote_id=quote.id,
        cart_id=quote.cart_id,
        subtotal=quote.subtotal,
        discount=quote.discount,
        shipping=quote.shipping,
        tax=quote.tax,
        total=quote.total,
        currency=quote.currency,
        quote_hash=quote.quote_hash,
        expires_at=quote.expires_at,
        created_at=quote.created_at,
        line_items_snapshot=quote.line_items_snapshot,
    )


@router.get("/{quote_id}", response_model=QuoteResponse)
def get_quote(quote_id: uuid.UUID, db: Session = Depends(get_db)):
    service = QuoteService(db)
    quote = service.get_quote_by_id(quote_id)
    return QuoteResponse(
        quote_id=quote.id,
        cart_id=quote.cart_id,
        subtotal=quote.subtotal,
        discount=quote.discount,
        shipping=quote.shipping,
        tax=quote.tax,
        total=quote.total,
        currency=quote.currency,
        quote_hash=quote.quote_hash,
        expires_at=quote.expires_at,
        created_at=quote.created_at,
        line_items_snapshot=quote.line_items_snapshot,
    )


@router.post("/{quote_id}/validate", response_model=QuoteValidationResponse)
def validate_quote(quote_id: uuid.UUID, db: Session = Depends(get_db)):
    service = QuoteService(db)
    valid, expired, quote = service.validate_quote(quote_id)
    return QuoteValidationResponse(
        valid=valid,
        expired=expired,
        amount=quote.total,
        currency=quote.currency,
    )
