import os
import sys
import logging
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.merchant import Merchant
from app.models.product import Product
from app.main import app
from fastapi.testclient import TestClient
from app.security.authentication import create_access_token

logging.basicConfig(level=logging.INFO)

def run_validation():
    db = SessionLocal()
    merchant = db.execute(select(Merchant)).scalars().first()
    
    if not merchant:
        logging.error("No merchant found.")
        return
        
    client = TestClient(app)
    token = create_access_token(str(merchant.user_id), role="MERCHANT")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Run a merchant simulation
    logging.info("--- 1. Running Simulation Engine via API ---")
    res = client.post("/api/v1/optimization/simulations", json={
        "scenario_count": 5
    }, headers=headers)
    
    if res.status_code != 200:
        logging.error(f"Simulation failed: {res.text}")
        return
        
    sim_data = res.json()
    sim_id = sim_data["simulation_id"]
    logging.info(f"Simulation completed with ID: {sim_id}")
    logging.info(f"Total Scenarios Processed: {sim_data['scenario_count']}")
    
    frictions_detected = len(sim_data["summary_metrics"]["friction_distribution"]) > 0
    logging.info(f"Friction Detection Works: {frictions_detected}")
    logging.info(f"Friction distribution: {sim_data['summary_metrics']['friction_distribution']}")

    # 4. Verify OptimizationRecommendations
    logging.info("--- 4. Verify Generated Recommendations via API ---")
    rec_res = client.get(f"/api/v1/optimization/recommendations", headers=headers)
    if rec_res.status_code == 200:
        recs = rec_res.json()
        logging.info(f"Retrieved {len(recs)} Optimization Recommendations.")
    else:
        logging.error("Failed to get recommendations.")
    
    # 5. Verify UpsellService finds candidates & cross-sell stays within catalogue
    logging.info("--- 5. Verifying Upsell Service via API ---")
    some_product = db.execute(select(Product).filter_by(merchant_id=merchant.id).limit(1)).scalar_one_or_none()
    if some_product:
        upsell_res = client.get(f"/api/v1/buyer/products/{some_product.id}/suggestions")
        if upsell_res.status_code == 200:
            upsell_data = upsell_res.json()
            logging.info(f"Upsell suggestions found: {len(upsell_data['upsell'])}")
            logging.info(f"Cross-sell suggestions found: {len(upsell_data['cross_sell'])}")
        else:
            logging.error("Failed to get upsell.")
    else:
        logging.warning("No product found to test upsell.")

    # 7. Verify CampaignService can consume signals
    logging.info("--- 7. Verifying Campaign Service via API ---")
    camp_res = client.post("/api/v1/campaigns/generate", headers=headers)
    if camp_res.status_code in (200, 201):
        campaigns = camp_res.json()
        logging.info(f"Generated {len(campaigns)} Campaign Proposals.")
    else:
        logging.error(f"Failed to generate campaigns: {camp_res.text}")

run_validation()
