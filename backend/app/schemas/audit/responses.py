import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    actor_type: str
    actor_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
    event_type: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    event_data: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
