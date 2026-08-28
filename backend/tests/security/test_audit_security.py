import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_system_audit_log_requires_admin():
    response = client.get("/api/v1/audit")
    assert response.status_code in [401, 403], "Audit logs are exposed to unauthenticated users!"
