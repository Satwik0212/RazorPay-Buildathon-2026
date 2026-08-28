import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.constants import ActorType


class AuditEventCreate(BaseModel):
    actor_type: ActorType
    actor_id: Optional[uuid.UUID] = None
    merchant_id: Optional[uuid.UUID] = None
    event_type: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: Optional[uuid.UUID] = None
    event_data: Dict[str, Any] = Field(default_factory=dict)
