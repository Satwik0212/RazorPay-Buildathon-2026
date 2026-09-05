from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.core.constants import UserRole


class RegisterRequest(BaseModel):
    name: str = Field(default="User", min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default=UserRole.CUSTOMER.value)

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Optional[str]) -> str:
        if not v:
            return UserRole.CUSTOMER.value
        v_upper = str(v).strip().upper()
        if v_upper in ("MERCHANT", "SELLER"):
            return UserRole.MERCHANT.value
        if v_upper in ("BUYER", "CUSTOMER"):
            return UserRole.CUSTOMER.value
        return v_upper


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
