from tests.helpers import create_test_merchant
import uuid
import pytest


def test_simulation_api_end_to_end(client, db_session):
    # 1. Register merchant user
    unique_email = f"merchant_sim_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = create_test_merchant(db_session, unique_email, "Password123!")
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get merchant profile
    merchant_res = client.get("/api/v1/merchants/me", headers=headers)
    assert merchant_res.status_code == 200
    merchant_id = merchant_res.json()["id"]

    # 3. Create products in database
    p1_res = client.post(
        "/api/v1/products",
        json={
            "name": "Budget Wireless Earbuds",
            "description": "Standard wireless audio buds",
            "category": "headphones",
            "price": 199900,
            "currency": "INR",
            "metadata": {"delivery_days": 5, "rating": 4.1, "return_days": 7}
        },
        headers=headers
    )
    assert p1_res.status_code == 201

    p2_res = client.post(
        "/api/v1/products",
        json={
            "name": "Flagship Pro ANC Headphones",
            "description": "Ultra fast delivery noise cancelling headphones with 30-day returns",
            "category": "headphones",
            "price": 899900,
            "currency": "INR",
            "metadata": {"delivery_days": 1, "rating": 4.9, "warranty": True, "return_days": 30, "anc": True}
        },
        headers=headers
    )
    assert p2_res.status_code == 201

    # 4. Run multi-persona simulation
    sim_res = client.post(
        "/api/v1/optimization/simulations",
        json={
            "merchant_id": merchant_id,
            "scenario_count": 4,
            "buyer_profiles": ["BUDGET", "SPEED", "QUALITY", "BALANCED"],
        },
        headers=headers
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["status"] == "COMPLETED"
    assert sim_data["scenario_count"] == 4
    assert len(sim_data["results"]) == 4
    assert "summary_metrics" in sim_data
    assert sim_data["summary_metrics"]["metric_type"] == "SIMULATED RESULT"

    # 5. Fetch explainable recommendations
    recs_res = client.get(
        "/api/v1/optimization/recommendations",
        headers=headers
    )
    assert recs_res.status_code == 200
    recs = recs_res.json()
    assert isinstance(recs, list)

    # 6. Run what-if optimization experiment
    what_if_res = client.post(
        "/api/v1/optimization/what-if",
        json={
            "merchant_id": merchant_id,
            "hypothesis": "Offering 1-day express delivery across all products improves speed-buyer matches",
            "modifications": {
                "delivery_days": 1,
                "metadata": {"express_shipping": True}
            }
        },
        headers=headers
    )
    assert what_if_res.status_code == 200
    what_if_data = what_if_res.json()
    assert "delta_percentage" in what_if_data
    assert what_if_data["baseline_metrics"]["metric_type"] == "SIMULATED RESULT"

def test_merchant_isolation_and_lifecycle(client, db_session):
    # 1. Register Merchant A
    unique_email_a = f"merchant_a_{uuid.uuid4().hex[:8]}@example.com"
    reg_a = create_test_merchant(db_session, unique_email_a, "Password123!")
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    merch_a_id = client.get("/api/v1/merchants/me", headers=headers_a).json()["id"]

    # 2. Register Merchant B
    unique_email_b = f"merchant_b_{uuid.uuid4().hex[:8]}@example.com"
    reg_b = create_test_merchant(db_session, unique_email_b, "Password123!")
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    merch_b_id = client.get("/api/v1/merchants/me", headers=headers_b).json()["id"]

    # 3. Create product for A that triggers a friction
    client.post("/api/v1/products", json={
        "name": "Friction Product",
        "description": "Short",
        "category": "test",
        "price": 100000,
        "currency": "INR",
        "metadata": {}  # Missing delivery and return triggers friction
    }, headers=headers_a)

    # 4. Run simulation as Merchant A but inject Merchant B ID (Testing isolation override)
    sim_a = client.post("/api/v1/optimization/simulations", json={
        "merchant_id": merch_b_id, # Attempt to override
        "scenario_count": 2,
    }, headers=headers_a)
    assert sim_a.status_code == 200
    sim_run_id = sim_a.json()["simulation_id"]
    assert sim_a.json()["merchant_id"] == merch_a_id # Should fall back/override to authenticated merchant

    # 5. Fetch A recommendations, there should be some due to frictions
    recs_a = client.get("/api/v1/optimization/recommendations", headers=headers_a).json()
    assert len(recs_a) > 0
    rec = recs_a[0]
    assert rec["simulation_run_id"] == sim_run_id # Traceability
    
    # 6. Fetch B recommendations, should be empty
    recs_b = client.get("/api/v1/optimization/recommendations", headers=headers_b).json()
    assert len(recs_b) == 0

    # 7. Lifecycle - B tries to update A recommendation
    patch_b = client.patch(f"/api/v1/optimization/recommendations/{rec['id']}/status", json={"status": "APPLIED"}, headers=headers_b)
    assert patch_b.status_code == 404 # Not found or not owned

    # 8. Lifecycle - A updates A recommendation
    patch_a = client.patch(f"/api/v1/optimization/recommendations/{rec['id']}/status", json={"status": "APPLIED"}, headers=headers_a)
    assert patch_a.status_code == 200
    assert patch_a.json()["status"] == "APPLIED"


def test_recommendation_application_semantics(client, db_session):
    import uuid
    # Register merchant
    unique_email = f"merchant_c_{uuid.uuid4().hex[:8]}@example.com"
    reg = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    merch_id = client.get("/api/v1/merchants/me", headers=headers).json()["id"]

    # Create a product
    p_res = client.post("/api/v1/products", json={
        "name": "Target Product",
        "description": "Desc",
        "category": "test",
        "price": 100000,
        "currency": "INR",
        "metadata": {"delivery_days": 5}
    }, headers=headers)
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    from app.models.optimization_recommendation import OptimizationRecommendation
    
    # 1. Advisory recommendation
    advisory_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="PRICE_ADVISORY",
        title="Lower Price",
        reason="It is expensive",
        action_data={"suggested_change": "Lower it by 5%"},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(advisory_rec)

    # 2. Explicit Executable recommendation
    executable_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="DELIVERY_FIX",
        title="Fix Delivery",
        reason="Too slow",
        action_data={"new_delivery_days": 2, "new_price": 95000},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(executable_rec)
    
    # 3. Rejected recommendation target
    reject_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="REJECT_ME",
        title="Reject me",
        reason="Bad idea",
        action_data={"new_price": 1000},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(reject_rec)
    db_session.commit()

    advisory_id = str(advisory_rec.id)
    executable_id = str(executable_rec.id)
    reject_id = str(reject_rec.id)


def test_recommendation_application_semantics(client, db_session):
    import uuid
    # Register merchant
    unique_email = f"merchant_c_{uuid.uuid4().hex[:8]}@example.com"
    reg = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    merch_id = client.get("/api/v1/merchants/me", headers=headers).json()["id"]

    # Create a product
    p_res = client.post("/api/v1/products", json={
        "name": "Target Product",
        "description": "Desc",
        "category": "test",
        "price": 100000,
        "currency": "INR",
        "metadata": {"delivery_days": 5}
    }, headers=headers)
    assert p_res.status_code == 201
    prod_id = p_res.json()["id"]

    from app.models.optimization_recommendation import OptimizationRecommendation
    
    # 1. Advisory recommendation
    advisory_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="PRICE_ADVISORY",
        title="Lower Price",
        reason="It is expensive",
        action_data={"suggested_change": "Lower it by 5%"},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(advisory_rec)

    # 2. Explicit Executable recommendation
    executable_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="DELIVERY_FIX",
        title="Fix Delivery",
        reason="Too slow",
        action_data={"new_delivery_days": 2, "new_price": 95000},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(executable_rec)
    
    # 3. Rejected recommendation target
    reject_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        product_id=uuid.UUID(prod_id),
        type="REJECT_ME",
        title="Reject me",
        reason="Bad idea",
        action_data={"new_price": 1000},
        status="PROPOSED",
        confidence=0.9,
        expected_simulated_impact=0.1
    )
    db_session.add(reject_rec)
    db_session.commit()

    advisory_id = str(advisory_rec.id)
    executable_id = str(executable_rec.id)
    reject_id = str(reject_rec.id)

    # Test A: Advisory recommendation
    patch_adv = client.patch(f"/api/v1/optimization/recommendations/{advisory_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert patch_adv.status_code == 200
    
    # Check product remains unchanged
    p_check_1 = client.get(f"/api/v1/products/{prod_id}", headers=headers).json()
    assert p_check_1["price"] == 100000
    assert p_check_1["metadata"]["delivery_days"] == 5

    # Test B: Explicit executable recommendation
    patch_exec = client.patch(f"/api/v1/optimization/recommendations/{executable_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert patch_exec.status_code == 200
    
    # Check product mutated correctly
    p_check_2 = client.get(f"/api/v1/products/{prod_id}", headers=headers).json()
    assert p_check_2["price"] == 95000
    assert p_check_2["metadata"]["delivery_days"] == 2

    # Test C: Idempotency
    client.patch(f"/api/v1/products/{prod_id}", json={"price": 80000}, headers=headers)
    patch_exec_2 = client.patch(f"/api/v1/optimization/recommendations/{executable_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert patch_exec_2.status_code == 200
    
    p_check_3 = client.get(f"/api/v1/products/{prod_id}", headers=headers).json()
    assert p_check_3["price"] == 80000

    # Test D: Rejection
    patch_rej = client.patch(f"/api/v1/optimization/recommendations/{reject_id}/status", json={"status": "REJECTED"}, headers=headers)
    assert patch_rej.status_code == 200
    
    p_check_4 = client.get(f"/api/v1/products/{prod_id}", headers=headers).json()
    assert p_check_4["price"] == 80000

    patch_rej_2 = client.patch(f"/api/v1/optimization/recommendations/{reject_id}/status", json={"status": "REJECTED"}, headers=headers)
    assert patch_rej_2.status_code == 200

def test_recommendation_apply_audit(client, db_session):
    import uuid
    # Register merchant
    unique_email = f"merchant_audit_{uuid.uuid4().hex[:8]}@example.com"
    reg = create_test_merchant(db_session, unique_email, "Password123!")
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    merch_id = client.get("/api/v1/merchants/me", headers=headers).json()["id"]

    # Create two products
    p1_res = client.post("/api/v1/products", json={
        "name": "Prod 1", "description": "Desc 1", "category": "test", "price": 100000, "currency": "INR", "metadata": {"delivery_days": 5}
    }, headers=headers)
    p2_res = client.post("/api/v1/products", json={
        "name": "Prod 2", "description": "Desc 2", "category": "test", "price": 200000, "currency": "INR", "metadata": {"delivery_days": 10}
    }, headers=headers)
    p1_id = p1_res.json()["id"]
    p2_id = p2_res.json()["id"]

    from app.models.optimization_recommendation import OptimizationRecommendation
    from app.models.audit_event import AuditEvent
    
    # Executable recommendation targeting both products via affected_product_ids
    exec_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        type="DELIVERY_UNKNOWN",
        title="Add Delivery",
        reason="Friction",
        action_data={"new_delivery_days": 2, "affected_product_ids": [p1_id, p2_id]},
        status="PROPOSED",
        confidence=1.0,
        expected_simulated_impact=1.0
    )
    db_session.add(exec_rec)
    db_session.commit()
    rec_id = str(exec_rec.id)

    # Apply
    res = client.patch(f"/api/v1/optimization/recommendations/{rec_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert res.status_code == 200

    # Verify products were updated
    p1_check = client.get(f"/api/v1/products/{p1_id}", headers=headers).json()
    assert p1_check["metadata"]["delivery_days"] == 2
    p2_check = client.get(f"/api/v1/products/{p2_id}", headers=headers).json()
    assert p2_check["metadata"]["delivery_days"] == 2

    # Verify audit events
    audits = db_session.query(AuditEvent).filter(
        AuditEvent.merchant_id == uuid.UUID(merch_id),
        AuditEvent.event_type == "RECOMMENDATION_APPLIED"
    ).all()
    assert len(audits) == 2
    
    audit_p1 = next(a for a in audits if str(a.entity_id) == p1_id)
    assert audit_p1.event_type == "RECOMMENDATION_APPLIED"
    assert audit_p1.event_data["recommendation_id"] == rec_id
    assert audit_p1.event_data["before_state"]["delivery_days"] == 5
    assert audit_p1.event_data["after_state"]["delivery_days"] == 2

    # Idempotent re-apply
    res_2 = client.patch(f"/api/v1/optimization/recommendations/{rec_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert res_2.status_code == 200
    
    # Should not create new audit events because nothing changed
    audits_after = db_session.query(AuditEvent).filter(
        AuditEvent.merchant_id == uuid.UUID(merch_id),
        AuditEvent.event_type == "RECOMMENDATION_APPLIED"
    ).all()
    assert len(audits_after) == 2

    # Verify GET audit endpoint
    audit_res = client.get("/api/v1/merchant/audit", headers=headers)
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["items"]
    assert any(a["event_type"] == "RECOMMENDATION_APPLIED" and a["entity_id"] == p1_id for a in audit_items)

    # Test B: Legacy recommendation fallback
    p3_res = client.post("/api/v1/products", json={
        "name": "Prod 3 Legacy", "description": "Desc 3", "category": "test", "price": 300000, "currency": "INR", "metadata": {"delivery_days": 10}
    }, headers=headers)
    p3_id = p3_res.json()["id"]

    legacy_rec = OptimizationRecommendation(
        merchant_id=uuid.UUID(merch_id),
        type="DELIVERY_UNKNOWN",
        title="Add Delivery Legacy",
        reason="Friction",
        action_data={"affected_product_ids": [p3_id]}, # Missing new_delivery_days
        status="PROPOSED",
        confidence=1.0,
        expected_simulated_impact=1.0
    )
    db_session.add(legacy_rec)
    db_session.commit()
    legacy_rec_id = str(legacy_rec.id)

    res_legacy = client.patch(f"/api/v1/optimization/recommendations/{legacy_rec_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert res_legacy.status_code == 200

    p3_check = client.get(f"/api/v1/products/{p3_id}", headers=headers).json()
    assert p3_check["metadata"]["delivery_days"] == 2

    audits_legacy = db_session.query(AuditEvent).filter(
        AuditEvent.merchant_id == uuid.UUID(merch_id),
        AuditEvent.event_type == "RECOMMENDATION_APPLIED",
        AuditEvent.entity_id == uuid.UUID(p3_id)
    ).all()
    assert len(audits_legacy) == 1
