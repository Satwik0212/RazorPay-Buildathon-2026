import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError, ForbiddenError
from app.core.constants import UserRole
from app.models.merchant import User, Merchant
from app.models.customer import Customer
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.customer_repository import CustomerRepository

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    user_id: uuid.UUID,
    role: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedError("Authentication token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Could not validate authentication token.") from exc


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise UnauthorizedError("Missing Bearer authorization header.")

    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token claims.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        raise UnauthorizedError("Invalid user ID format in token.") from exc

    repo = MerchantRepository(db)
    user = repo.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("User account not found or deactivated.")
    return user


def get_current_merchant(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Merchant:
    if user.role != UserRole.MERCHANT.value and user.role != UserRole.ADMIN.value:
        raise ForbiddenError("Merchant role required for this action.")

    repo = MerchantRepository(db)
    merchant = repo.get_merchant_by_user_id(user.id)
    if not merchant or not merchant.is_active:
        raise ForbiddenError("Merchant profile not found or inactive.")
    return merchant


def get_current_customer(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Customer:
    if user.role != UserRole.CUSTOMER.value and user.role != UserRole.ADMIN.value:
        raise ForbiddenError("Customer role required for this action.")

    repo = CustomerRepository(db)
    customer = repo.get_by_user_id(user.id)
    if not customer:
        # Automatically initialize customer profile if needed
        customer = repo.create(Customer(user_id=user.id))
    return customer
