import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.audit_event import AuditEvent


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, event: AuditEvent) -> AuditEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_events(
        self,
        merchant_id: Optional[uuid.UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AuditEvent], int]:
        stmt = select(AuditEvent).order_by(AuditEvent.created_at.desc())
        count_stmt = select(func.count(AuditEvent.id))

        filters = []
        if merchant_id:
            filters.append(AuditEvent.merchant_id == merchant_id)
        if entity_type:
            filters.append(AuditEvent.entity_type == entity_type)
        if entity_id:
            filters.append(AuditEvent.entity_id == entity_id)
        if event_type:
            filters.append(AuditEvent.event_type == event_type)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.db.execute(count_stmt).scalar() or 0
        events = list(self.db.execute(stmt.limit(limit).offset(offset)).scalars().all())
        return events, total
