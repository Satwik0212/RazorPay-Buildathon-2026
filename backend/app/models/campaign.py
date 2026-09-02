import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import String, ForeignKey, Uuid, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase
from app.core.constants import CampaignStatus

class Campaign(ModelBase):
    __tablename__ = "campaigns"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    objective: Mapped[str] = mapped_column(String(500), nullable=False)
    campaign_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=CampaignStatus.PROPOSED.value, nullable=False)
    
    target_persona_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("buyer_personas.id", ondelete="SET NULL"), nullable=True)
    target_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    
    trigger_signal: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
