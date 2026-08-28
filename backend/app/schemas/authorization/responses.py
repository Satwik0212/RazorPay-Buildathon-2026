import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuthorizationResponse(BaseModel):
    authorization_id: uuid.UUID
    quote_id: uuid.UUID
    customer_id: uuid.UUID
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
