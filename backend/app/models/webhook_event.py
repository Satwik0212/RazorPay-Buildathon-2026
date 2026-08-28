from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import String, Boolean, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase, utc_now


class WebhookEvent(ModelBase):
    __tablename__ = "webhook_events"

    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
