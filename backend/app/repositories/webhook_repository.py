import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.webhook_event import WebhookEvent


class WebhookRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: uuid.UUID) -> Optional[WebhookEvent]:
        return self.db.get(WebhookEvent, id)

    def get_by_event_id(self, event_id: str) -> Optional[WebhookEvent]:
        stmt = select(WebhookEvent).where(WebhookEvent.event_id == event_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def create(self, event: WebhookEvent) -> WebhookEvent:
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def mark_processed(self, event_id: str, error: Optional[str] = None) -> Optional[WebhookEvent]:
        event = self.get_by_event_id(event_id)
        if event:
            event.processed = True
            event.processed_at = datetime.now(timezone.utc)
            event.processing_error = error
            self.db.commit()
            self.db.refresh(event)
        return event
