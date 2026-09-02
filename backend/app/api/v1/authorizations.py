import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.authorization.requests import AuthorizationCreate
from app.schemas.authorization.responses import AuthorizationResponse
from app.services.authorization_service import AuthorizationService
from app.security.authentication import get_current_customer
from app.models.customer import Customer

router = APIRouter(prefix="/authorizations", tags=["Authorizations"])


@router.post("", response_model=AuthorizationResponse, status_code=status.HTTP_201_CREATED)
def create_authorization(
    req: AuthorizationCreate,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
):
    service = AuthorizationService(db)
    auth = service.authorize_quote(quote_id=req.quote_id, customer_id=current_customer.id)
    return AuthorizationResponse(
        authorization_id=auth.id,
        quote_id=auth.quote_id,
        customer_id=auth.customer_id,
        amount=auth.amount,
        currency=auth.currency,
        status=auth.status,
        created_at=auth.created_at,
        updated_at=auth.updated_at,
    )


from app.core.exceptions import ForbiddenError

@router.get("/{authorization_id}", response_model=AuthorizationResponse)
def get_authorization(
    authorization_id: uuid.UUID,
    current_customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db)
):
    service = AuthorizationService(db)
    auth = service.get_authorization_by_id(authorization_id)
    if auth.customer_id != current_customer.id:
        raise ForbiddenError("You cannot access this authorization.")
    return AuthorizationResponse(
        authorization_id=auth.id,
        quote_id=auth.quote_id,
        customer_id=auth.customer_id,
        amount=auth.amount,
        currency=auth.currency,
        status=auth.status,
        created_at=auth.created_at,
        updated_at=auth.updated_at,
    )
