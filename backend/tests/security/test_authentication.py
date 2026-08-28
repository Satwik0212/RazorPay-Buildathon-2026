import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_missing_credentials():
    response = client.get("/api/v1/merchants/me")
    assert response.status_code == 401

def test_invalid_credentials():
    response = client.get("/api/v1/merchants/me", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

def test_malformed_tokens():
    response = client.get("/api/v1/merchants/me", headers={"Authorization": "Bearer malformed.jwt.token"})
    assert response.status_code == 401

def test_expired_credentials():
    # Simulate an expired token
    expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJtZXJjaGFudDEiLCJleHAiOjEwMDAwMDAwMDB9.invalid"
    response = client.get("/api/v1/merchants/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401

def test_unauthorized_routes():
    # A customer trying to access merchant routes
    customer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0b21lcjEiLCJyb2xlIjoiQ1VTVE9NRVIifQ.invalid"
    response = client.get("/api/v1/merchants/me", headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code in [401, 403]

def test_privilege_escalation():
    # A customer attempting to update merchant catalog
    customer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjdXN0b21lcjEiLCJyb2xlIjoiQ1VTVE9NRVIifQ.invalid"
    response = client.post("/api/v1/products", json={"name": "Hacked Product"}, headers={"Authorization": f"Bearer {customer_token}"})
    assert response.status_code in [401, 403]
