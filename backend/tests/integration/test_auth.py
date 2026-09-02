import pytest


def test_auth_registration_and_login_flow(client):
    # 1. Register Customer
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer_api@test.com",
            "password": "password12345",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["user"]["email"] == "customer_api@test.com"
    assert reg_data["user"]["role"] == "CUSTOMER"
    assert "access_token" in reg_data
    token = reg_data["access_token"]

    # 2. Access /api/v1/auth/me
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "customer_api@test.com"

    # 3. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "customer_api@test.com",
            "password": "password12345",
        },
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()

    # 4. Duplicate registration fails with 409 Conflict
    dup_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": "customer_api@test.com",
            "password": "password12345",
        },
    )
    assert dup_resp.status_code == 409
