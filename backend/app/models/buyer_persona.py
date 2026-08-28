from typing import List
from sqlalchemy import String, BigInteger, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase


class BuyerPersona(ModelBase):
    __tablename__ = "buyer_personas"

    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    budget_min: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    budget_max: Mapped[int] = mapped_column(BigInteger, default=1000000, nullable=False)
    priorities: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    urgency: Mapped[str] = mapped_column(String(50), default="MEDIUM", nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
