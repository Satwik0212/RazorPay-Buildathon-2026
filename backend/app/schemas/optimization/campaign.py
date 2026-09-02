import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import CampaignStatus

class CampaignBase(BaseModel):
    name: str
    objective: str
    campaign_type: str
    target_persona_id: Optional[uuid.UUID] = None
    target_product_id: Optional[uuid.UUID] = None
    trigger_signal: str
    trigger_evidence: Dict[str, Any]
    message_content: str

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    objective: Optional[str] = None
    message_content: Optional[str] = None

class CampaignStatusUpdate(BaseModel):
    status: CampaignStatus

class CampaignResponse(CampaignBase):
    id: uuid.UUID
    merchant_id: uuid.UUID
    status: CampaignStatus
    activated_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
