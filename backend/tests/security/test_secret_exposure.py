import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_no_secrets_in_errors():
    response = client.get("/api/v1/products/invalid_uuid")
    data = response.text
    assert "password" not in data.lower()
    assert "secret" not in data.lower()
    assert "traceback" not in data.lower()
    assert "sqlalchemy" not in data.lower()

def test_env_files_ignored():
    import os
    if os.path.exists(".gitignore"):
        with open(".gitignore", "r") as f:
            content = f.read()
            assert ".env" in content, ".env is not ignored in .gitignore"
