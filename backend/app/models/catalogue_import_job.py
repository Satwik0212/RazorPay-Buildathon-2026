import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, JSON, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import ModelBase


class CatalogueImportJob(ModelBase):
    """
    Merchant-scoped import job. Stores analysis between analyze and confirm steps.
    merchant_id is set from authenticated session, NEVER from CSV content.
    """
    __tablename__ = "catalogue_import_jobs"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="ANALYZED", nullable=False, index=True
    )
    schema_type: Mapped[str] = mapped_column(String(100), nullable=False, default="UNKNOWN")
    ai_mapper_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_mapper_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    has_low_confidence_mappings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    ready_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    needs_review_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    needs_fix_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # We will need to map valid_row_count and invalid_row_count to something or delete them. Wait, since it's an existing DB we need alembic migration.
    # Wait, maybe it's easier to just keep valid_row_count and invalid_row_count in the model but add the new ones, or recreate the db table. If we are in dev we might drop or alter.
    valid_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    invalid_row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    analysis_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    import_result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

