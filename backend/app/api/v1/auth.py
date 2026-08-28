from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth.requests import RegisterRequest, LoginRequest
from app.schemas.auth.responses import AuthResponse, UserResponse
from app.services.auth_service import AuthService
from app.security.authentication import get_current_user
from app.models.merchant import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user, token = service.register(req)
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            merchant_id=user.merchant.id if user.merchant else None,
            customer_id=user.customer.id if user.customer else None,
        ),
        access_token=token,
        token_type="bearer",
    )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user, token = service.login(req)
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            merchant_id=user.merchant.id if user.merchant else None,
            customer_id=user.customer.id if user.customer else None,
        ),
        access_token=token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        merchant_id=current_user.merchant.id if current_user.merchant else None,
        customer_id=current_user.customer.id if current_user.customer else None,
    )
