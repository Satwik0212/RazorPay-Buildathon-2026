import uuid
from typing import Dict, Any
from sqlalchemy import String, Float, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase


class WhatIfRun(ModelBase):
    __tablename__ = "what_if_runs"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    hypothesis: Mapped[str] = mapped_column(String(500), nullable=False)
    modifications: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    baseline_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    simulated_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    delta_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
