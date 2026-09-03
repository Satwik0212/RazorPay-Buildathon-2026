import uuid
import pytest
from app.models.product import Product, Inventory
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService
from tests.helpers import create_test_merchant


@pytest.fixture
def test_merchants(db_session):
    res_a = create_test_merchant(db_session, email="merch_a@example.com")
    res_b = create_test_merchant(db_session, email="merch_b@example.com")
    merchant_a_id = uuid.UUID(res_a.json()["user"]["merchant_id"])
    merchant_b_id = uuid.UUID(res_b.json()["user"]["merchant_id"])
    return merchant_a_id, merchant_b_id


class TestActiveCatalogueRetrieval:
    """
    Focused unit tests for Optimization Step 3: Full Active Catalogue Retrieval.
    Verifies full retrieval, merchant isolation, inactive filtering, and truthful inventory semantics.
    """

    def test_full_catalogue_retrieval_exceeds_legacy_limits(self, db_session, test_merchants):
        """
        Verify that retrieval returns ALL active products without legacy 100/50 limits.
        Creates 120 products (>100 legacy limit) and ensures all 120 are retrieved.
        """
        merchant_a_id, _ = test_merchants
        repo = ProductRepository(db_session)
        service = ProductService(db_session)

        # Create 120 active products with inventory
        for i in range(120):
            p = Product(
                merchant_id=merchant_a_id,
                name=f"Product {i:03d}",
                description=f"Description for product {i}",
                category="Electronics",
                price=1000 + i * 10,
                currency="INR",
                is_active=True,
                product_metadata={"delivery_days": 2, "index": i},
            )
            db_session.add(p)
            db_session.flush()
            inv = Inventory(
                product_id=p.id,
                available_quantity=i + 1,
                reserved_quantity=0,
            )
            db_session.add(inv)
        db_session.commit()

        # Repository retrieval
        catalogue_repo = repo.get_active_catalogue_for_merchant(merchant_a_id)
        assert len(catalogue_repo) == 120, f"Expected 120 products, got {len(catalogue_repo)}"

        # Service retrieval
        catalogue_service = service.get_active_catalogue(merchant_a_id)
        assert len(catalogue_service) == 120
        assert catalogue_repo == catalogue_service

        # Deterministic ordering by Product.id
        ids = [p["id"] for p in catalogue_repo]
        assert ids == sorted(ids), "Catalogue must be sorted deterministically by Product.id"

    def test_inactive_products_are_strictly_excluded(self, db_session, test_merchants):
        """
        Verify that inactive products (is_active=False) are excluded from the catalogue.
        """
        merchant_a_id, _ = test_merchants
        repo = ProductRepository(db_session)

        # 3 active, 2 inactive
        for i in range(3):
            p = Product(
                merchant_id=merchant_a_id,
                name=f"Active Product {i}",
                description="Active",
                category="Gadgets",
                price=5000,
                currency="INR",
                is_active=True,
                product_metadata={},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=10, reserved_quantity=0))

        for i in range(2):
            p_inactive = Product(
                merchant_id=merchant_a_id,
                name=f"Inactive Product {i}",
                description="Inactive",
                category="Gadgets",
                price=5000,
                currency="INR",
                is_active=False,
                product_metadata={},
            )
            db_session.add(p_inactive)
            db_session.flush()
            db_session.add(Inventory(product_id=p_inactive.id, available_quantity=10, reserved_quantity=0))
        db_session.commit()

        catalogue = repo.get_active_catalogue_for_merchant(merchant_a_id)
        assert len(catalogue) == 3
        for item in catalogue:
            assert item["is_active"] is True
            assert "Active Product" in item["name"]

    def test_strict_merchant_isolation(self, db_session, test_merchants):
        """
        Verify that products belonging to other merchants are never retrieved.
        """
        merchant_a_id, merchant_b_id = test_merchants
        repo = ProductRepository(db_session)

        # Add 5 products for merchant A
        for i in range(5):
            p = Product(
                merchant_id=merchant_a_id,
                name=f"Merchant A Product {i}",
                description="A",
                category="Books",
                price=2000,
                currency="INR",
                is_active=True,
                product_metadata={},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=5, reserved_quantity=0))

        # Add 4 products for merchant B
        for i in range(4):
            p = Product(
                merchant_id=merchant_b_id,
                name=f"Merchant B Product {i}",
                description="B",
                category="Books",
                price=2500,
                currency="INR",
                is_active=True,
                product_metadata={},
            )
            db_session.add(p)
            db_session.flush()
            db_session.add(Inventory(product_id=p.id, available_quantity=8, reserved_quantity=0))
        db_session.commit()

        cat_a = repo.get_active_catalogue_for_merchant(merchant_a_id)
        cat_b = repo.get_active_catalogue_for_merchant(merchant_b_id)

        assert len(cat_a) == 5
        assert len(cat_b) == 4

        a_names = {item["name"] for item in cat_a}
        b_names = {item["name"] for item in cat_b}

        assert all("Merchant A" in name for name in a_names)
        assert all("Merchant B" in name for name in b_names)
        assert a_names.isdisjoint(b_names)

    def test_truthful_inventory_semantics(self, db_session, test_merchants):
        """
        Verify truthful inventory semantics:
        - In-stock product retains exact positive available_quantity.
        - Out-of-stock product (available_quantity=0) returns exactly 0 (NOT fabricated 10, NOT None).
        - Missing inventory row returns None (NOT fabricated 10).
        """
        merchant_a_id, _ = test_merchants
        repo = ProductRepository(db_session)

        # 1. Product with positive inventory
        p_in_stock = Product(
            merchant_id=merchant_a_id,
            name="In Stock Item",
            description="Has stock",
            category="InventoryTest",
            price=1500,
            currency="INR",
            is_active=True,
            product_metadata={"tag": "in_stock"},
        )
        db_session.add(p_in_stock)
        db_session.flush()
        db_session.add(Inventory(product_id=p_in_stock.id, available_quantity=42, reserved_quantity=0))

        # 2. Product with zero inventory (out of stock)
        p_zero_stock = Product(
            merchant_id=merchant_a_id,
            name="Zero Stock Item",
            description="Out of stock",
            category="InventoryTest",
            price=1500,
            currency="INR",
            is_active=True,
            product_metadata={"tag": "zero_stock"},
        )
        db_session.add(p_zero_stock)
        db_session.flush()
        db_session.add(Inventory(product_id=p_zero_stock.id, available_quantity=0, reserved_quantity=0))

        # 3. Product with missing inventory row (untracked / unmanaged)
        p_missing_inv = Product(
            merchant_id=merchant_a_id,
            name="Missing Inventory Item",
            description="No inventory row exists",
            category="InventoryTest",
            price=1500,
            currency="INR",
            is_active=True,
            product_metadata={"tag": "missing_inventory"},
        )
        db_session.add(p_missing_inv)
        db_session.flush()
        # Deliberately DO NOT add an Inventory row for p_missing_inv

        db_session.commit()

        catalogue = repo.get_active_catalogue_for_merchant(merchant_a_id)
        assert len(catalogue) == 3

        cat_by_id = {item["id"]: item for item in catalogue}

        # Case 1: Positive stock
        assert cat_by_id[p_in_stock.id]["available_quantity"] == 42

        # Case 2: Out of stock (0 must remain 0, never coalesced to 10)
        assert cat_by_id[p_zero_stock.id]["available_quantity"] == 0
        assert cat_by_id[p_zero_stock.id]["available_quantity"] is not None

        # Case 3: Missing inventory row must be None (never coalesced to 10, never coalesced to 0)
        assert cat_by_id[p_missing_inv.id]["available_quantity"] is None

    def test_catalogue_field_structure_and_defaults(self, db_session, test_merchants):
        """
        Verify all required fields exist with correct types and default fallbacks
        (e.g., None description becomes "", None metadata becomes {}).
        """
        merchant_a_id, _ = test_merchants
        repo = ProductRepository(db_session)

        p = Product(
            merchant_id=merchant_a_id,
            name="Default Handling Item",
            description="",
            category="StructureTest",
            price=9999,
            currency="INR",
            is_active=True,
            product_metadata={},
        )
        db_session.add(p)
        db_session.flush()
        db_session.add(Inventory(product_id=p.id, available_quantity=15, reserved_quantity=0))
        db_session.commit()

        catalogue = repo.get_active_catalogue_for_merchant(merchant_a_id)
        assert len(catalogue) == 1
        item = catalogue[0]

        expected_keys = {
            "id", "name", "description", "category", "price",
            "currency", "is_active", "product_metadata", "available_quantity"
        }
        assert set(item.keys()) == expected_keys

        assert isinstance(item["id"], uuid.UUID)
        assert isinstance(item["name"], str)
        assert isinstance(item["description"], str)
        assert isinstance(item["category"], str)
        assert isinstance(item["price"], int)
        assert isinstance(item["currency"], str)
        assert isinstance(item["is_active"], bool)
        assert isinstance(item["product_metadata"], dict)
        assert item["available_quantity"] == 15
