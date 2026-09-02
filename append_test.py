with open('backend/tests/integration/test_optimization.py', 'a') as f:
    f.write('''

def test_recommendation_application_semantics(client, db_session):
    import uuid
    # Register merchant
    unique_email = f"merchant_c_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/api/v1/auth/register", json={"email": unique_email, "password": "Password123!", "role": "MERCHANT"})
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
    assert p_check_1["product_metadata"]["delivery_days"] == 5

    # Test B: Explicit executable recommendation
    patch_exec = client.patch(f"/api/v1/optimization/recommendations/{executable_id}/status", json={"status": "APPLIED"}, headers=headers)
    assert patch_exec.status_code == 200
    
    # Check product mutated correctly
    p_check_2 = client.get(f"/api/v1/products/{prod_id}", headers=headers).json()
    assert p_check_2["price"] == 95000
    assert p_check_2["product_metadata"]["delivery_days"] == 2

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
''')
