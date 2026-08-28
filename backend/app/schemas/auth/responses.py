import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    role: str
    is_active: bool
    merchant_id: Optional[uuid.UUID] = None
    customer_id: Optional[uuid.UUID] = None

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
