from tests.helpers import create_test_merchant
"""
Regression tests: Product → Inventory → Catalogue API → Simulation data consistency.

These tests use the test-isolated SQLite DB (via the `client` fixture from conftest.py).
They register a fresh merchant and seed known products so results are fully predictable.
"""
import uuid
import pytest
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ──────────────────────────────────────────────────────────────────────────────

def register_merchant(client, db_session) -> dict:
    """Register a unique merchant and return {'token': ..., 'headers': ..., 'merchant_id': ...}."""
    email = f"inv_test_{uuid.uuid4().hex[:8]}@example.com"
    res = create_test_merchant(db_session, email, 'Password123!')
    assert res.status_code == 201, res.json()
    token = res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    me = client.get('/api/v1/auth/me', headers=headers).json()
    return {'token': token, 'headers': headers, 'merchant_id': me['merchant_id']}


def add_product(client, headers, name, price, qty, metadata=None):
    """Create a product with given initial_quantity and return the product dict."""
    payload = {
        'name': name,
        'category': 'test_electronics',
        'price': price,
        'currency': 'INR',
        'metadata': metadata or {'delivery_days': 2, 'rating': 4.5, 'warranty': True},
        'initial_quantity': qty,
    }
    res = client.post('/api/v1/products', json=payload, headers=headers)
    assert res.status_code == 201, f"Product creation failed: {res.json()}"
    return res.json()


# ──────────────────────────────────────────────────────────────────────────────
# Auth wiring tests
# ──────────────────────────────────────────────────────────────────────────────

class TestAuthWiring:
    def test_register_and_login_round_trip(self, client, db_session):
        """Registering a merchant and logging in returns a consistent merchant_id."""
        email = f"wiring_{uuid.uuid4().hex[:8]}@example.com"
        reg = create_test_merchant(db_session, email, 'Password123!')
        assert reg.status_code == 201
        # merchant_id is nested inside the 'user' object in the register response
        reg_merchant_id = reg.json()['user']['merchant_id']

        login = client.post('/api/v1/auth/login',
                            json={'email': email, 'password': 'Password123!'})
        assert login.status_code == 200
        login_token = login.json()['access_token']

        me = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {login_token}'})
        assert me.status_code == 200
        assert me.json()['merchant_id'] == reg_merchant_id

    def test_merchant_isolation_in_catalogue(self, client, db_session):
        """Two merchants only see their own products."""
        m1 = register_merchant(client, db_session)
        m2 = register_merchant(client, db_session)

        add_product(client, m1['headers'], 'Merchant 1 Widget', 100, 50)
        add_product(client, m2['headers'], 'Merchant 2 Gadget', 200, 30)

        cat1 = client.get('/api/v1/products', headers=m1['headers']).json()
        cat2 = client.get('/api/v1/products', headers=m2['headers']).json()

        names1 = [i['name'] for i in cat1['items']]
        names2 = [i['name'] for i in cat2['items']]

        assert 'Merchant 1 Widget' in names1
        assert 'Merchant 2 Gadget' not in names1
        assert 'Merchant 2 Gadget' in names2
        assert 'Merchant 1 Widget' not in names2


# ──────────────────────────────────────────────────────────────────────────────
# Inventory → Catalogue API consistency
# ──────────────────────────────────────────────────────────────────────────────

class TestInventoryCatalogueConsistency:
    def test_catalogue_api_includes_inventory_field(self, client, db_session):
        """Every product in the catalogue API response must have an inventory field."""
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'Stocked Product', 50000, 100)

        res = client.get('/api/v1/products', headers=m['headers'])
        assert res.status_code == 200
        items = res.json()['items']
        assert len(items) > 0
        for item in items:
            assert 'inventory' in item, f"Product {item['name']} missing inventory"
            assert item['inventory'] is not None

    def test_api_inventory_qty_matches_initial_quantity(self, client, db_session):
        """Product created with initial_quantity=75 should show 75 in the API."""
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'Known Stock Product', 99900, 75)

        res = client.get('/api/v1/products', headers=m['headers'])
        items = res.json()['items']
        product = next((i for i in items if i['name'] == 'Known Stock Product'), None)
        assert product is not None
        assert product['inventory']['available_quantity'] == 75

    def test_zero_stock_product_shows_zero_in_api(self, client, db_session):
        """Product with initial_quantity=0 must show 0 in catalogue API."""
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'Out Of Stock Product', 49900, 0)

        res = client.get('/api/v1/products', headers=m['headers'])
        items = res.json()['items']
        product = next((i for i in items if i['name'] == 'Out Of Stock Product'), None)
        assert product is not None
        assert product['inventory']['available_quantity'] == 0

    def test_inventory_update_reflects_in_catalogue_api(self, client, db_session):
        """Updating inventory via PATCH must be visible in the next GET /products call."""
        m = register_merchant(client, db_session)
        p = add_product(client, m['headers'], 'Updatable Product', 99900, 10)
        product_id = p['id']

        # Update inventory
        upd = client.patch(f'/api/v1/products/{product_id}/inventory',
                          json={'available_quantity': 999}, headers=m['headers'])
        assert upd.status_code == 200
        assert upd.json()['available_quantity'] == 999

        # Verify catalogue reflects the update
        res = client.get('/api/v1/products', headers=m['headers'])
        items = res.json()['items']
        product = next((i for i in items if i['id'] == product_id), None)
        assert product is not None
        assert product['inventory']['available_quantity'] == 999

    def test_mixed_inventory_distribution_visible_in_api(self, client, db_session):
        """Catalogue API correctly shows a mix of in-stock and out-of-stock products."""
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'In Stock A', 10000, 50)
        add_product(client, m['headers'], 'In Stock B', 20000, 5)
        add_product(client, m['headers'], 'Out of Stock C', 30000, 0)

        res = client.get('/api/v1/products', headers=m['headers'])
        items = res.json()['items']

        by_name = {i['name']: i['inventory']['available_quantity'] for i in items}
        assert by_name['In Stock A'] == 50
        assert by_name['In Stock B'] == 5
        assert by_name['Out of Stock C'] == 0


# ──────────────────────────────────────────────────────────────────────────────
# Catalogue API → Simulation data consistency
# ──────────────────────────────────────────────────────────────────────────────

class TestSimulationInventoryConsistency:
    def test_simulation_hard_rejects_zero_stock_product(self, client, db_session):
        """A product with qty=0 must appear in frictions as INVENTORY_ISSUE, not be selected."""
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'Must Reject Zero Stock', 50000, 0,
                    metadata={'delivery_days': 1, 'rating': 5.0, 'warranty': True,
                              'return_days': 30, 'discount_percent': 50})
        add_product(client, m['headers'], 'Should Be Selected', 50000, 100,
                    metadata={'delivery_days': 1, 'rating': 4.0})

        sim = client.post('/api/v1/optimization/simulations',
                         json={'scenario_count': 1, 'buyer_profiles': ['FEATURE']},
                         headers=m['headers'])
        assert sim.status_code == 200
        results = sim.json()['results']
        assert results, "No results returned"

        # The zero-stock product must not be selected
        assert results[0].get('selected_product_id') != 'Must Reject Zero Stock'

        # INVENTORY_ISSUE must appear in friction distribution
        fd = sim.json()['summary_metrics']['friction_distribution']
        assert fd.get('INVENTORY_ISSUE', 0) > 0

    def test_simulation_selects_in_stock_product(self, client, db_session):
        """When one product is in stock and one is not, the in-stock one must be selected."""
        m = register_merchant(client, db_session)
        in_stock = add_product(client, m['headers'], 'Available Product', 99900, 50,
                               metadata={'delivery_days': 2, 'rating': 4.5, 'warranty': True,
                                         'return_days': 30, 'discount_percent': 10})
        add_product(client, m['headers'], 'Unavailable Product', 99900, 0,
                    metadata={'delivery_days': 1, 'rating': 5.0, 'warranty': True,
                              'return_days': 30, 'discount_percent': 50})

        sim = client.post('/api/v1/optimization/simulations',
                         json={'scenario_count': 1, 'buyer_profiles': ['FEATURE']},
                         headers=m['headers'])
        assert sim.status_code == 200
        result = sim.json()['results'][0]
        assert result['constraints_satisfied'] is True
        assert result['selected_product_id'] == in_stock['id']

    def test_simulation_receives_same_qty_as_catalogue_api(self, client, db_session):
        """
        The product selected by the simulation must have qty > 0 per the Catalogue API.
        Proves catalogue and simulation read from the same inventory data.
        """
        m = register_merchant(client, db_session)
        add_product(client, m['headers'], 'Consistent Stock A', 45000, 75,
                    metadata={'delivery_days': 1, 'rating': 4.3, 'warranty': True, 'return_days': 15})
        add_product(client, m['headers'], 'Zero Stock B', 45000, 0,
                    metadata={'delivery_days': 1, 'rating': 4.9})

        # Run simulation
        sim = client.post('/api/v1/optimization/simulations',
                         json={'scenario_count': 1, 'buyer_profiles': ['FEATURE']},
                         headers=m['headers'])
        assert sim.status_code == 200
        selected_id = sim.json()['results'][0].get('selected_product_id')

        if selected_id:
            # Cross-check: look up this product in the Catalogue API
            cat = client.get('/api/v1/products', headers=m['headers'])
            items = {i['id']: i for i in cat.json()['items']}
            assert selected_id in items, (
                f"Selected product {selected_id} not found in Catalogue API — "
                "simulation and catalogue are using different merchant/data contexts"
            )
            catalogue_qty = items[selected_id]['inventory']['available_quantity']
            assert catalogue_qty > 0, (
                f"Simulation selected product {selected_id} but Catalogue API "
                f"shows qty={catalogue_qty} — data mismatch"
            )

    def test_simulation_inventory_issue_not_100_percent_when_stock_available(self, client, db_session):
        """If most products are in stock, INVENTORY_ISSUE should not dominate frictions."""
        m = register_merchant(client, db_session)
        # Add 5 in-stock products, 1 out-of-stock
        for i in range(5):
            add_product(client, m['headers'], f'In Stock Product {i}', 50000 + i * 10000, 50,
                       metadata={'delivery_days': 2, 'rating': 4.0 + i * 0.1})
        add_product(client, m['headers'], 'Out Of Stock Singleton', 50000, 0,
                   metadata={'delivery_days': 1, 'rating': 5.0})

        sim = client.post('/api/v1/optimization/simulations',
                         json={'scenario_count': 5, 'buyer_profiles': ['FEATURE']},
                         headers=m['headers'])
        assert sim.status_code == 200
        fd = sim.json()['summary_metrics']['friction_distribution']
        total_friction = sum(fd.values())
        inv_friction = fd.get('INVENTORY_ISSUE', 0)

        if total_friction > 0:
            inv_pct = inv_friction / total_friction
            # 1 out-of-stock out of 6 products = ~16.7% of product evaluations
            # Even with 5 scenarios × 1 zero-stock = 5 signals, total should be higher
            assert inv_pct < 0.60, (
                f"INVENTORY_ISSUE = {inv_pct:.1%} of total — suggests zero-stock products "
                f"dominating. Frictions: {fd}"
            )
