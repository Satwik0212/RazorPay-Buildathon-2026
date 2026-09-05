"""
Integration tests for the Catalogue Import API.
Tests analyze + confirm flow end-to-end against real SQLite test DB.
Uses conftest.py fixtures: client, db_session.
"""
import io
import csv
import uuid
import pytest
from tests.helpers import create_test_merchant


def make_csv_bytes(rows: list) -> bytes:
    """Helper: build a CSV bytes string from a list of dicts."""
    if not rows:
        return b"product_name,price\n"
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


def _flipkart_row(name: str, uniq_id: str = None) -> dict:
    return {
        "uniq_id": uniq_id or f"u-{uuid.uuid4().hex[:8]}",
        "crawl_timestamp": "", "product_url": "",
        "product_name": name,
        "product_category_tree": '["Computers >> Test Category"]',
        "pid": "", "retail_price": "2000", "discounted_price": "1500",
        "image": '["http://img.example.com/1.jpg"]',
        "is_FK_Advantage_product": "FALSE",
        "description": "A test product with sufficient description text for import",
        "product_rating": "4.5", "overall_rating": "4.2",
        "brand": "TestBrand",
        "product_specifications": '{"product_specification"=>[{"key"=>"Color", "value"=>"Black"}]}',
    }


class TestAnalyzeFlipkartCSV:
    def test_flipkart_canonical_fast_path(self, client, db_session):
        """Flipkart CSV recognized deterministically without LLM."""
        resp = create_test_merchant(db_session, f"merchant_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        csv_bytes = make_csv_bytes([_flipkart_row("Test Headphone Pro")])
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers=headers,
            files={"file": ("catalogue.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["schema_type"] == "FLIPKART_CANONICAL"
        assert data["ai_mapper_used"] == False
        assert data["ready_row_count"] == 1
        assert data["needs_fix_row_count"] == 0
        assert data["import_job_id"]

        target_fields = [m["target_field"] for m in data["mappings"]]
        assert "product_name" in target_fields
        assert "discounted_price" in target_fields
        assert "brand" in target_fields

    def test_rejects_non_csv(self, client, db_session):
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("evil.xlsx", b"fake content", "application/octet-stream")},
        )
        assert resp.status_code == 400

    def test_requires_auth(self, client, db_session):
        csv_bytes = make_csv_bytes([_flipkart_row("Test")])
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code in (401, 403)

    def test_rejects_file_exceeding_50mb(self, client, db_session):
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        # 50MB + 10 bytes file
        huge_bytes = b"product_name,price\n" + (b"x" * (50 * 1024 * 1024 - 10))
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("huge.csv", huge_bytes, "text/csv")},
        )
        assert resp.status_code == 413
        assert "50MB" in resp.json()["detail"]


class TestAnalyzeAndConfirmFlow:
    def test_confirm_creates_products(self, client, db_session):
        """Full analyze+confirm creates real products in DB."""
        from sqlalchemy import select
        from app.models.product import Product

        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unique_name = f"Integration Product {uuid.uuid4().hex[:8]}"
        csv_bytes = make_csv_bytes([_flipkart_row(unique_name)])

        # Step 1: Analyze
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers=headers,
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200, resp.text
        import_job_id = resp.json()["import_job_id"]
        assert resp.json()["ready_row_count"] == 1

        # Step 2: Confirm
        resp2 = client.post(
            "/api/v1/catalogue/import/confirm",
            headers=headers,
            json={"import_job_id": import_job_id, "confirmed": True},
        )
        assert resp2.status_code == 200, resp2.text
        result = resp2.json()
        assert result["status"] == "COMPLETED"
        assert result["inserted"] == 1
        assert result["failed"] == 0

        # Verify real DB record
        product = db_session.execute(
            select(Product).filter(Product.name == unique_name)
        ).scalar_one_or_none()
        assert product is not None
        assert product.price == 150000  # 1500 rupees * 100 paise
        assert product.currency == "INR"
        assert product.merchant_id is not None  # came from session, not CSV

    def test_merchant_isolation_on_confirm(self, client, db_session):
        """Merchant B cannot confirm Merchant A's import job."""
        resp_a = create_test_merchant(db_session, f"a_{uuid.uuid4().hex[:6]}@test.com")
        resp_b = create_test_merchant(db_session, f"b_{uuid.uuid4().hex[:6]}@test.com")
        token_a = resp_a.json()["access_token"]
        token_b = resp_b.json()["access_token"]

        csv_bytes = make_csv_bytes([_flipkart_row(f"Merchant A Product {uuid.uuid4().hex[:6]}")])

        # Merchant A analyzes
        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"file": ("a.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200
        job_id = resp.json()["import_job_id"]

        # Merchant B tries to confirm
        resp2 = client.post(
            "/api/v1/catalogue/import/confirm",
            headers={"Authorization": f"Bearer {token_b}"},
            json={"import_job_id": job_id, "confirmed": True},
        )
        assert resp2.status_code in (403, 404), resp2.text

    def test_duplicate_skipped_on_reimport(self, client, db_session):
        """Re-importing the same product skips it (idempotent)."""
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        unique_name = f"Dedup Product {uuid.uuid4().hex[:8]}"
        csv_bytes = make_csv_bytes([_flipkart_row(unique_name)])

        # First import
        r1 = client.post("/api/v1/catalogue/import/analyze", headers=headers,
                         files={"file": ("t.csv", csv_bytes, "text/csv")})
        assert r1.status_code == 200
        job_id1 = r1.json()["import_job_id"]

        r2 = client.post("/api/v1/catalogue/import/confirm", headers=headers,
                         json={"import_job_id": job_id1, "confirmed": True})
        assert r2.status_code == 200
        assert r2.json()["inserted"] == 1

        # Second import same CSV
        r3 = client.post("/api/v1/catalogue/import/analyze", headers=headers,
                         files={"file": ("t.csv", csv_bytes, "text/csv")})
        assert r3.status_code == 200
        job_id2 = r3.json()["import_job_id"]

        r4 = client.post("/api/v1/catalogue/import/confirm", headers=headers,
                         json={"import_job_id": job_id2, "confirmed": True})
        assert r4.status_code == 200
        assert r4.json()["inserted"] == 0
        assert r4.json()["skipped_existing"] == 1

    def test_invalid_product_skipped(self, client, db_session):
        """Rows with no price are rejected and counted as invalid."""
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        row = _flipkart_row("Priceless Product")
        row["retail_price"] = ""
        row["discounted_price"] = ""
        csv_bytes = make_csv_bytes([row])

        resp = client.post(
            "/api/v1/catalogue/import/analyze",
            headers=headers,
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        assert resp.status_code == 200
        assert resp.json()["ready_row_count"] == 0
        assert resp.json()["needs_fix_row_count"] == 1

    def test_merchant_id_never_from_csv(self, client, db_session):
        """Even if CSV contains a merchant_id column, it must be ignored."""
        from sqlalchemy import select
        from app.models.product import Product

        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Include a merchant_id column in CSV - it must be IGNORED
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=[
            "product_name", "discounted_price", "retail_price",
            "category", "description", "merchant_id"
        ])
        writer.writeheader()
        writer.writerow({
            "product_name": f"Security Test {uuid.uuid4().hex[:8]}",
            "discounted_price": "1000",
            "retail_price": "1200",
            "category": "Electronics",
            "description": "Security test product with description",
            "merchant_id": "00000000-0000-0000-0000-000000000000",  # FAKE merchant_id
        })
        csv_bytes = buf.getvalue().encode("utf-8")

        r1 = client.post("/api/v1/catalogue/import/analyze", headers=headers,
                         files={"file": ("sec.csv", csv_bytes, "text/csv")})
        # If analyzed OK...
        if r1.status_code == 200 and r1.json()["ready_row_count"] > 0:
            job_id = r1.json()["import_job_id"]
            r2 = client.post("/api/v1/catalogue/import/confirm", headers=headers,
                             json={"import_job_id": job_id, "confirmed": True})
            if r2.status_code == 200 and r2.json()["inserted"] > 0:
                product = db_session.execute(
                    select(Product).filter(Product.name.contains("Security Test"))
                ).scalar_one_or_none()
                if product:
                    # Must be the actual merchant, never the fake one
                    assert str(product.merchant_id) != "00000000-0000-0000-0000-000000000000"
