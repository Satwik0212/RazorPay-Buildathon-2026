from fastapi import APIRouter, Request, Header, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.webhook.responses import WebhookProcessResult
from app.services.webhook_service import WebhookService
from app.core.exceptions import WebhookSignatureError

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", response_model=WebhookProcessResult)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
):
    if not x_razorpay_signature:
        raise WebhookSignatureError("Missing X-Razorpay-Signature header.")

    # Read raw body bytes directly before any parsing
    raw_body = await request.body()

    service = WebhookService(db)
    is_duplicate, event_id, message = service.process_razorpay_webhook(
        raw_body=raw_body,
        signature=x_razorpay_signature,
    )

    return WebhookProcessResult(
        status="success",
        message=message,
        event_id=event_id,
        duplicate=is_duplicate,
    )
