import uuid
from typing import Optional, Dict, Any
from sqlalchemy import String, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase


class AuditEvent(ModelBase):
    __tablename__ = "audit_events"

    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    event_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
