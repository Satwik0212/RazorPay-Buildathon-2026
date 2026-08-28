import uuid
from pydantic import BaseModel


class CheckoutOrderCreate(BaseModel):
    quote_id: uuid.UUID
    authorization_id: uuid.UUID
