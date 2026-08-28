import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, ForeignKey, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import ModelBase

if TYPE_CHECKING:
    from app.models.merchant import Merchant


class Policy(ModelBase):
    __tablename__ = "policies"

    merchant_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), unique=True, nullable=False)
    max_autonomous_amount: Mapped[int] = mapped_column(BigInteger, default=500000, nullable=False)  # e.g. ₹5,000.00
    daily_autonomous_limit: Mapped[int] = mapped_column(BigInteger, default=5000000, nullable=False)  # e.g. ₹50,000.00
    require_approval_above: Mapped[int] = mapped_column(BigInteger, default=500000, nullable=False)
    blocked_categories: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    is_ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="policy")
