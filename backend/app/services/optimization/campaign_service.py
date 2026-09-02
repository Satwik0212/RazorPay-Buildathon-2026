import uuid
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc
from fastapi import HTTPException, status
from app.models.campaign import Campaign
from app.models.simulation_run import SimulationRun
from app.models.simulation_result import SimulationResult
from app.models.optimization_recommendation import OptimizationRecommendation
from app.models.buyer_persona import BuyerPersona
from app.models.product import Product
from app.schemas.optimization.campaign import CampaignCreate, CampaignUpdate, CampaignStatusUpdate
from app.core.constants import CampaignStatus
from app.integrations.llm.client import llm_client

class CampaignService:
    def __init__(self, db: Session):
        self.db = db

    def generate_campaign_proposals(self, merchant_id: uuid.UUID) -> List[Campaign]:
        # Detect genuine opportunities from real DB data
        # Fetch recent recommendations
        stmt_recs = select(OptimizationRecommendation).where(
            OptimizationRecommendation.merchant_id == merchant_id
        ).order_by(desc(OptimizationRecommendation.created_at)).limit(50)
        recs = self.db.execute(stmt_recs).scalars().all()

        # Fetch recent simulation results for this merchant's runs
        stmt_sims = select(SimulationResult).join(SimulationRun).where(
            SimulationRun.merchant_id == merchant_id
        ).order_by(desc(SimulationResult.created_at)).limit(100)
        sim_results = self.db.execute(stmt_sims).scalars().all()

        if not recs and not sim_results:
            return []

        proposals = []
        
        # Strategy 1: Generate from recommendations
        for rec in recs:
            # We want to create one campaign per recommendation type that hasn't been created yet
            existing = self.db.execute(select(Campaign).where(
                and_(
                    Campaign.merchant_id == merchant_id,
                    Campaign.trigger_signal == rec.type,
                    Campaign.target_product_id == rec.product_id
                )
            )).scalars().first()
            
            if existing:
                continue
                
            persona_id = None
            if rec.simulation_run_id:
                run = self.db.execute(select(SimulationRun).where(SimulationRun.id == rec.simulation_run_id)).scalars().first()
                if run and run.buyer_profiles:
                    bp = self.db.execute(select(BuyerPersona).where(BuyerPersona.name == run.buyer_profiles[0])).scalars().first()
                    if bp:
                        persona_id = bp.id
                    
            # Use LLM to generate wording
            prompt = f"""
            Generate a short, engaging campaign message for an ecommerce store.
            The issue we are addressing is: {rec.title} ({rec.reason}).
            The goal is to improve conversion rates for this segment.
            Return ONLY the text of the message, nothing else.
            """
            system_prompt = "You are an expert ecommerce marketing assistant."
            
            message_content = llm_client.generate_text(prompt, system_prompt)
            if not message_content or len(message_content) < 10:
                message_content = f"Special Offer! We noticed some issues with {rec.title}. Check out our updated offerings!"
                
            campaign = Campaign(
                merchant_id=merchant_id,
                name=f"Optimization: {rec.title[:100]}",
                objective=f"Address {rec.type} to improve conversions",
                campaign_type="RECOMMENDATION_DRIVEN",
                status=CampaignStatus.PROPOSED.value,
                target_persona_id=persona_id,
                target_product_id=rec.product_id,
                trigger_signal=rec.type,
                trigger_evidence={
                    "recommendation_id": str(rec.id),
                    "confidence": rec.confidence,
                    "expected_impact": rec.expected_simulated_impact
                },
                message_content=message_content
            )
            self.db.add(campaign)
            proposals.append(campaign)
            
            # Limit to 3 proposals to avoid spamming
            if len(proposals) >= 3:
                break
                
        # Strategy 2: High friction simulations
        if len(proposals) < 3:
            for sim in sim_results:
                if sim.score < 0.5 and sim.frictions:
                    friction = sim.frictions[0]
                    friction_type = friction.get("type", "UNKNOWN_FRICTION")
                    
                    existing = self.db.execute(select(Campaign).where(
                        and_(
                            Campaign.merchant_id == merchant_id,
                            Campaign.trigger_signal == friction_type,
                            Campaign.target_product_id == sim.selected_product_id
                        )
                    )).scalars().first()
                    
                    if existing:
                        continue
                        
                    bp = self.db.execute(select(BuyerPersona).where(BuyerPersona.name == sim.persona_name)).scalars().first()
                    persona_id = bp.id if bp else None
                    
                    prompt = f"""
                    Generate a short, engaging campaign message for an ecommerce store to overcome customer friction.
                    The customer experienced this friction: {friction.get('description', friction_type)}.
                    Return ONLY the text of the message, nothing else.
                    """
                    
                    message_content = llm_client.generate_text(prompt, "You are an expert ecommerce marketing assistant.")
                    if not message_content or len(message_content) < 10:
                        message_content = f"We've improved our shopping experience regarding {friction_type.replace('_', ' ')}. Check it out!"
                        
                    campaign = Campaign(
                        merchant_id=merchant_id,
                        name=f"Friction Recovery: {friction_type}",
                        objective=f"Overcome {friction_type} friction",
                        campaign_type="FRICTION_RECOVERY",
                        status=CampaignStatus.PROPOSED.value,
                        target_persona_id=persona_id,
                        target_product_id=sim.selected_product_id,
                        trigger_signal=friction_type,
                        trigger_evidence={
                            "simulation_result_id": str(sim.id),
                            "score": sim.score,
                            "friction": friction
                        },
                        message_content=message_content
                    )
                    self.db.add(campaign)
                    proposals.append(campaign)
                    
                    if len(proposals) >= 3:
                        break

        self.db.commit()
        for p in proposals:
            self.db.refresh(p)
            
        return proposals

    def list_campaigns(self, merchant_id: uuid.UUID) -> List[Campaign]:
        stmt = select(Campaign).where(Campaign.merchant_id == merchant_id).order_by(desc(Campaign.created_at))
        return list(self.db.execute(stmt).scalars().all())

    def get_campaign(self, campaign_id: uuid.UUID, merchant_id: uuid.UUID) -> Campaign:
        stmt = select(Campaign).where(
            and_(Campaign.id == campaign_id, Campaign.merchant_id == merchant_id)
        )
        campaign = self.db.execute(stmt).scalars().first()
        if not campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        return campaign

    def update_campaign_status(self, campaign_id: uuid.UUID, merchant_id: uuid.UUID, status_update: CampaignStatusUpdate) -> Campaign:
        campaign = self.get_campaign(campaign_id, merchant_id)
        
        current_status = CampaignStatus(campaign.status)
        new_status = status_update.status
        
        # State machine validation
        valid_transitions = {
            CampaignStatus.PROPOSED: [CampaignStatus.ACTIVE, CampaignStatus.REJECTED],
            CampaignStatus.ACTIVE: [CampaignStatus.PAUSED, CampaignStatus.ENDED],
            CampaignStatus.PAUSED: [CampaignStatus.ACTIVE, CampaignStatus.ENDED],
            CampaignStatus.REJECTED: [],
            CampaignStatus.ENDED: []
        }
        
        if new_status not in valid_transitions.get(current_status, []):
            if current_status != new_status:  # Allow idempotent updates
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail=f"Invalid transition from {current_status.value} to {new_status.value}"
                )
        
        campaign.status = new_status.value
        
        # Update timestamps based on transition
        if new_status == CampaignStatus.ACTIVE and current_status == CampaignStatus.PROPOSED:
            from datetime import timezone
            campaign.activated_at = datetime.now(timezone.utc)
        elif new_status == CampaignStatus.ENDED:
            from datetime import timezone
            campaign.ended_at = datetime.now(timezone.utc)
            
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
