import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class MerchantResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
