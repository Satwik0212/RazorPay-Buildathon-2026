import uuid
from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.merchant import Merchant
from app.security.authentication import get_current_merchant
from app.schemas.optimization.campaign import CampaignResponse, CampaignStatusUpdate
from app.services.optimization.campaign_service import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Optimization Campaigns"])

@router.post("/generate", response_model=List[CampaignResponse], status_code=status.HTTP_201_CREATED)
def generate_campaigns(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Detects opportunities from simulation records and generates proposed campaigns."""
    service = CampaignService(db)
    return service.generate_campaign_proposals(current_merchant.id)

@router.get("", response_model=List[CampaignResponse])
def list_campaigns(
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """List all campaigns for the authenticated merchant."""
    service = CampaignService(db)
    return service.list_campaigns(current_merchant.id)

@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: uuid.UUID,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Get a specific campaign."""
    service = CampaignService(db)
    return service.get_campaign(campaign_id, current_merchant.id)

@router.patch("/{campaign_id}/status", response_model=CampaignResponse)
def update_campaign_status(
    campaign_id: uuid.UUID,
    status_update: CampaignStatusUpdate,
    current_merchant: Merchant = Depends(get_current_merchant),
    db: Session = Depends(get_db)
):
    """Update campaign status securely (PROPOSED -> ACTIVE -> PAUSED -> ENDED)."""
    service = CampaignService(db)
    return service.update_campaign_status(campaign_id, current_merchant.id, status_update)
