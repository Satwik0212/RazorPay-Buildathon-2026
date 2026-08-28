import uuid
from pydantic import BaseModel


class AuthorizationCreate(BaseModel):
    quote_id: uuid.UUID
