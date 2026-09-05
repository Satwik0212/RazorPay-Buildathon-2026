import pytest
import uuid
from tests.integration.test_catalogue_import_api import create_test_merchant, make_csv_bytes, _flipkart_row

class TestReviewAndResolveFlow:
    def test_review_and_resolve_flow(self, client, db_session):
        """End-to-end test of analyzing, reviewing issues, resolving them, and confirming."""
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a CSV with one good row and one bad row (missing price)
        good_row = _flipkart_row("Good Product")
        bad_row = _flipkart_row("Bad Product")
        bad_row["retail_price"] = ""; bad_row["discounted_price"] = ""
        bad_row["discounted_price"] = ""

        csv_bytes = make_csv_bytes([good_row, bad_row])

        # 1. Analyze
        r1 = client.post(
            "/api/v1/catalogue/import/analyze",
            headers=headers,
            files={"file": ("test.csv", csv_bytes, "text/csv")},
        )
        assert r1.status_code == 200
        data = r1.json()
        job_id = data["import_job_id"]

        assert data["ready_row_count"] == 1
        assert data["needs_fix_row_count"] == 1

        # 2. Try to confirm (should fail because unresolved issues)
        r_conf = client.post(
            "/api/v1/catalogue/import/confirm",
            headers=headers,
            json={"import_job_id": job_id, "confirmed": True},
        )
        assert r_conf.status_code == 400
        assert "Cannot confirm import with unresolved issues" in r_conf.json()["detail"]

        # 3. Get review rows
        r_review = client.get(f"/api/v1/catalogue/import/{job_id}/review", headers=headers)
        assert r_review.status_code == 200
        review_rows = r_review.json()["rows"]
        assert len(review_rows) == 1
        assert review_rows[0]["status"] == "NEEDS_FIX"
        assert review_rows[0]["normalized_candidate"]["product_name"] == "Bad Product"
        row_idx = review_rows[0]["row_index"]

        # 4. Try to accept a NEEDS_FIX row (should fail)
        r_accept = client.patch(
            f"/api/v1/catalogue/import/{job_id}/rows/{row_idx}",
            headers=headers,
            json={"action": "ACCEPT"}
        )
        assert r_accept.status_code == 400

        # 5. Fix the row via EDIT
        r_edit = client.patch(
            f"/api/v1/catalogue/import/{job_id}/rows/{row_idx}",
            headers=headers,
            json={"action": "EDIT", "updated_fields": {"retail_price": 500, "discounted_price": 400}}
        )
        assert r_edit.status_code == 200
        assert r_edit.json()["row"]["status"] == "READY"

        # 6. Check review rows again (should be empty since no filter defaults to not READY/EXCLUDED)
        r_review2 = client.get(f"/api/v1/catalogue/import/{job_id}/review", headers=headers)
        assert len(r_review2.json()["rows"]) == 0

        # 7. Confirm now works
        r_conf2 = client.post(
            "/api/v1/catalogue/import/confirm",
            headers=headers,
            json={"import_job_id": job_id, "confirmed": True},
        )
        assert r_conf2.status_code == 200
        assert r_conf2.json()["inserted"] == 2

    def test_exclude_row(self, client, db_session):
        resp = create_test_merchant(db_session, f"m_{uuid.uuid4().hex[:6]}@test.com")
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        bad_row = _flipkart_row("Bad Product 2")
        bad_row["retail_price"] = ""; bad_row["discounted_price"] = ""
        csv_bytes = make_csv_bytes([bad_row])

        r1 = client.post("/api/v1/catalogue/import/analyze", headers=headers, files={"file": ("test.csv", csv_bytes, "text/csv")})
        job_id = r1.json()["import_job_id"]

        r_review = client.get(f"/api/v1/catalogue/import/{job_id}/review", headers=headers)
        row_idx = r_review.json()["rows"][0]["row_index"]

        r_exclude = client.patch(
            f"/api/v1/catalogue/import/{job_id}/rows/{row_idx}",
            headers=headers,
            json={"action": "EXCLUDE"}
        )
        assert r_exclude.status_code == 200

        r_conf = client.post("/api/v1/catalogue/import/confirm", headers=headers, json={"import_job_id": job_id, "confirmed": True})
        assert r_conf.status_code == 200
        assert r_conf.json()["inserted"] == 0
        assert r_conf.json()["total_attempted"] == 0
