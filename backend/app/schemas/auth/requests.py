from pydantic import BaseModel, EmailStr, Field
from app.core.constants import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = Field(default=UserRole.CUSTOMER)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
