import uuid
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Float, Boolean, Integer, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.simulation_run import SimulationRun


class SimulationResult(ModelBase):
    __tablename__ = "simulation_results"

    simulation_run_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("simulation_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    persona_name: Mapped[str] = mapped_column(String(100), nullable=False)
    selected_product_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    constraints_satisfied: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reason_codes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    frictions: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    rankings: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(String(2000), default="", nullable=False)

    simulation_run: Mapped["SimulationRun"] = relationship("SimulationRun", back_populates="results")
