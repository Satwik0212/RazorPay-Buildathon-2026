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


def test_merchant_registration_with_name_and_role(client):
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Rajesh Kumar",
            "email": "rajesh_merchant@test.com",
            "password": "securepwd123",
            "role": "merchant",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["user"]["name"] == "Rajesh Kumar"
    assert reg_data["user"]["email"] == "rajesh_merchant@test.com"
    assert reg_data["user"]["role"] == "MERCHANT"
    assert reg_data["user"]["merchant_id"] is not None
    token = reg_data["access_token"]

    # Verify /api/v1/auth/me returns name and role
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Rajesh Kumar"
    assert me_data["role"] == "MERCHANT"

    # Verify login returns name and role
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "email": "rajesh_merchant@test.com",
            "password": "securepwd123",
        },
    )
    assert login_resp.status_code == 200
    assert login_resp.json()["user"]["name"] == "Rajesh Kumar"
    assert login_resp.json()["user"]["role"] == "MERCHANT"


def test_buyer_registration_with_name_and_role(client):
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Priya Sharma",
            "email": "priya_buyer@test.com",
            "password": "securepwd123",
            "role": "buyer",
        },
    )
    assert reg_resp.status_code == 201
    reg_data = reg_resp.json()
    assert reg_data["user"]["name"] == "Priya Sharma"
    assert reg_data["user"]["email"] == "priya_buyer@test.com"
    assert reg_data["user"]["role"] == "CUSTOMER"
    assert reg_data["user"]["customer_id"] is not None


def test_pydantic_validation_on_email_and_password(client):
    # Invalid email syntax fails Pydantic validation
    bad_email_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Invalid User",
            "email": "not-a-valid-email",
            "password": "validpassword123",
        },
    )
    assert bad_email_resp.status_code == 422

    # Password too short fails Pydantic validation (min length 8)
    short_pwd_resp = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Short Pwd",
            "email": "valid@email.com",
            "password": "short",
        },
    )
    assert short_pwd_resp.status_code == 422
