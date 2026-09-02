from tests.helpers import create_test_merchant
import pytest
import uuid
from fastapi import status
from sqlalchemy import select
from app.models.campaign import Campaign
from app.models.simulation_run import SimulationRun
from app.models.simulation_result import SimulationResult
from app.models.buyer_persona import BuyerPersona
from app.models.optimization_recommendation import OptimizationRecommendation
from app.core.constants import CampaignStatus
from app.api.v1.optimization.campaigns import router as campaigns_router
from app.main import app

app.include_router(campaigns_router, prefix="/api/v1/optimization")

@pytest.fixture
def auth_setup(client, db_session):
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    merchant_res = client.get("/api/v1/merchants/me", headers=headers)
    merchant_id = merchant_res.json()["id"]
    
    return {"client": client, "headers": headers, "merchant_id": merchant_id}

@pytest.fixture
def test_product(auth_setup, db_session):
    res = auth_setup["client"].post(
        "/api/v1/products",
        headers=auth_setup["headers"],
        json={
            "name": "Campaign Product",
            "description": "Test",
            "category": "laptop",
            "price": 100000,
            "currency": "INR"
        }
    )
    return res.json()

@pytest.fixture
def test_persona(auth_setup, db_session):
    res = auth_setup["client"].post(
        "/api/v1/optimization/personas",
        headers=auth_setup["headers"],
        json={
            "name": f"Test Persona {uuid.uuid4().hex[:8]}",
            "description": "Test",
            "budget_min": 0,
            "budget_max": 200000,
            "priorities": ["price"]
        }
    )
    # The optimization/personas might not be registered or works differently. Let's just create in DB.
    pass

@pytest.fixture
def db_persona(db_session):
    persona = BuyerPersona(
        name=f"Test Persona {uuid.uuid4().hex[:8]}",
        description="Test",
        budget_min=0,
        budget_max=200000,
        priorities=["price"]
    )
    db_session.add(persona)
    db_session.commit()
    db_session.refresh(persona)
    return persona

def test_generate_campaigns_empty(auth_setup, db_session):
    response = auth_setup["client"].post("/api/v1/optimization/campaigns/generate", headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == []

def test_generate_campaigns_with_friction(auth_setup, db_session, test_product, db_persona):
    merchant_id = uuid.UUID(auth_setup["merchant_id"])
    product_id = uuid.UUID(test_product["id"])
    
    sim_run = SimulationRun(
        merchant_id=merchant_id,
        
        status="COMPLETED"
    )
    db_session.add(sim_run)
    db_session.commit()
    db_session.refresh(sim_run)
    
    sim_result = SimulationResult(
        simulation_run_id=sim_run.id,
        persona_name=db_persona.name,
        selected_product_id=product_id,
        score=0.4,
        constraints_satisfied=False,
        reason_codes=["PRICE_TOO_HIGH"],
        frictions=[{"type": "PRICE_MISMATCH", "description": "Too expensive"}],
        rankings=[],
        explanation="Price too high"
    )
    db_session.add(sim_result)
    db_session.commit()
    
    response = auth_setup["client"].post("/api/v1/optimization/campaigns/generate", headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data) >= 1
    
    campaign = next(c for c in data if c["campaign_type"] == "FRICTION_RECOVERY")
    assert campaign["trigger_signal"] == "PRICE_MISMATCH"
    assert campaign["status"] == CampaignStatus.PROPOSED.value
    assert "simulation_result_id" in campaign["trigger_evidence"]
    assert "clicks" not in campaign["trigger_evidence"]

def test_generate_campaigns_with_recommendation(auth_setup, db_session, test_product):
    merchant_id = uuid.UUID(auth_setup["merchant_id"])
    product_id = uuid.UUID(test_product["id"])
    
    rec = OptimizationRecommendation(
        merchant_id=merchant_id,
        product_id=product_id,
        type="DELIVERY_UNCLEAR",
        title="Delivery time unclear",
        reason="Buyers dropped off",
        expected_simulated_impact=0.1
    )
    db_session.add(rec)
    db_session.commit()
    
    response = auth_setup["client"].post("/api/v1/optimization/campaigns/generate", headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    
    assert any(c["trigger_signal"] == "DELIVERY_UNCLEAR" for c in data)

def test_campaign_lifecycle(auth_setup, db_session):
    merchant_id = uuid.UUID(auth_setup["merchant_id"])
    campaign = Campaign(
        merchant_id=merchant_id,
        name="Test",
        objective="Test",
        campaign_type="TEST",
        status=CampaignStatus.PROPOSED.value,
        trigger_signal="TEST",
        message_content="Test message"
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    
    # PROPOSED -> ACTIVE
    response = auth_setup["client"].patch(f"/api/v1/optimization/campaigns/{campaign.id}/status", json={"status": "ACTIVE"}, headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ACTIVE"
    assert response.json()["activated_at"] is not None
    
    # ACTIVE -> PAUSED
    response = auth_setup["client"].patch(f"/api/v1/optimization/campaigns/{campaign.id}/status", json={"status": "PAUSED"}, headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "PAUSED"
    
    # PAUSED -> ACTIVE
    response = auth_setup["client"].patch(f"/api/v1/optimization/campaigns/{campaign.id}/status", json={"status": "ACTIVE"}, headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ACTIVE"

    # ACTIVE -> ENDED
    response = auth_setup["client"].patch(f"/api/v1/optimization/campaigns/{campaign.id}/status", json={"status": "ENDED"}, headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ENDED"
    assert response.json()["ended_at"] is not None

def test_invalid_lifecycle_transition(auth_setup, db_session):
    merchant_id = uuid.UUID(auth_setup["merchant_id"])
    campaign = Campaign(
        merchant_id=merchant_id,
        name="Test",
        objective="Test",
        campaign_type="TEST",
        status=CampaignStatus.PROPOSED.value,
        trigger_signal="TEST",
        message_content="Test message"
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    
    # PROPOSED -> ENDED is invalid
    response = auth_setup["client"].patch(f"/api/v1/optimization/campaigns/{campaign.id}/status", json={"status": "ENDED"}, headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_merchant_isolation(auth_setup, db_session):
    other_merchant_id = uuid.uuid4()
    campaign = Campaign(
        merchant_id=other_merchant_id,
        name="Test Other",
        objective="Test",
        campaign_type="TEST",
        status=CampaignStatus.PROPOSED.value,
        trigger_signal="TEST",
        message_content="Test message"
    )
    db_session.add(campaign)
    db_session.commit()
    db_session.refresh(campaign)
    
    response = auth_setup["client"].get(f"/api/v1/optimization/campaigns/{campaign.id}", headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_active_campaign_eligibility(auth_setup, db_session):
    merchant_id = uuid.UUID(auth_setup["merchant_id"])
    c1 = Campaign(
        merchant_id=merchant_id,
        name="C1",
        objective="O",
        campaign_type="T",
        status=CampaignStatus.ACTIVE.value,
        trigger_signal="S",
        message_content="M"
    )
    c2 = Campaign(
        merchant_id=merchant_id,
        name="C2",
        objective="O",
        campaign_type="T",
        status=CampaignStatus.PROPOSED.value,
        trigger_signal="S",
        message_content="M"
    )
    db_session.add_all([c1, c2])
    db_session.commit()
    
    response = auth_setup["client"].get("/api/v1/optimization/campaigns", headers=auth_setup["headers"])
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) >= 2
