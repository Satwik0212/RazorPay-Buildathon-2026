import uuid
from pydantic import BaseModel


class QuoteCreate(BaseModel):
    cart_id: uuid.UUID
