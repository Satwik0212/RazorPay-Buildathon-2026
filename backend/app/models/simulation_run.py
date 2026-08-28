import uuid
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase
from app.core.constants import SimulationStatus

if TYPE_CHECKING:
    from app.models.simulation_result import SimulationResult


class SimulationRun(ModelBase):
    __tablename__ = "simulation_runs"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=SimulationStatus.COMPLETED.value, nullable=False)
    scenario_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    buyer_profiles: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    summary_metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    results: Mapped[List["SimulationResult"]] = relationship("SimulationResult", back_populates="simulation_run", cascade="all, delete-orphan")
