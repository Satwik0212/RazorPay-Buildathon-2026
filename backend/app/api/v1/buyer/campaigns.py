import uuid
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.campaign import Campaign
from app.core.constants import CampaignStatus
from app.schemas.optimization.campaign import CampaignResponse

router = APIRouter(prefix="/buyer/campaigns", tags=["Buyer Campaigns"])

@router.get("", response_model=List[CampaignResponse])
def get_active_campaigns(
    merchant_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    stmt = select(Campaign).where(
        and_(
            Campaign.merchant_id == merchant_id,
            Campaign.status == CampaignStatus.ACTIVE.value
        )
    )
    campaigns = db.execute(stmt).scalars().all()
    return campaigns
