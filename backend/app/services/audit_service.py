import uuid
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.models.audit_event import AuditEvent
from app.repositories.audit_repository import AuditRepository
from app.core.logging import logger


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuditRepository(db)

    def log_event(
        self,
        event_type: str,
        actor_type: str,
        entity_type: str,
        actor_id: Optional[uuid.UUID] = None,
        merchant_id: Optional[uuid.UUID] = None,
        entity_id: Optional[uuid.UUID] = None,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """
        Creates an immutable audit log record on the server.
        """
        event = AuditEvent(
            actor_type=actor_type,
            actor_id=actor_id,
            merchant_id=merchant_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=event_data or {},
        )
        saved = self.repo.create(event)
        logger.info(
            f"[AUDIT] {event_type} on {entity_type}:{entity_id} by {actor_type}:{actor_id}"
        )
        return saved

    def list_events(
        self,
        merchant_id: Optional[uuid.UUID] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[uuid.UUID] = None,
        event_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[AuditEvent], int]:
        return self.repo.list_events(
            merchant_id=merchant_id,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            limit=limit,
            offset=offset,
        )
