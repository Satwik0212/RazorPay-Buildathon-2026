import uuid
from typing import Optional, Dict, Any
from sqlalchemy import String, Float, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase
from app.core.constants import RecommendationStatus


class OptimizationRecommendation(ModelBase):
    __tablename__ = "optimization_recommendations"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    simulation_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("simulation_runs.id", ondelete="SET NULL"), nullable=True)
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    action_data: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expected_simulated_impact: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=RecommendationStatus.PROPOSED.value, nullable=False)
