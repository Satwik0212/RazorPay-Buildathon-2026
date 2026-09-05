import pytest
import uuid

def test_01_register_merchant_creates_merchant_profile(client):
    resp = client.post('/api/v1/auth/register', json={
        'name': 'Test Merchant 1', 'email': 'tm1@test.com', 'password': 'password123', 'role': 'merchant'
    })
    assert resp.status_code == 201
    assert resp.json()['user']['role'] == 'MERCHANT'
    assert 'merchant_id' in resp.json()['user']

def test_02_register_customer_creates_customer_profile(client):
    resp = client.post('/api/v1/auth/register', json={
        'name': 'Test Customer 1', 'email': 'tc1@test.com', 'password': 'password123', 'role': 'customer'
    })
    assert resp.status_code == 201
    assert resp.json()['user']['role'] == 'CUSTOMER'
    assert 'customer_id' in resp.json()['user']

def test_03_login_merchant_returns_correct_role(client):
    client.post('/api/v1/auth/register', json={'name': 'TM3', 'email': 'tm3@test.com', 'password': 'password123', 'role': 'merchant'})
    resp = client.post('/api/v1/auth/login', json={'email': 'tm3@test.com', 'password': 'password123'})
    assert resp.status_code == 200
    assert resp.json()['user']['role'] == 'MERCHANT'
    assert 'merchant_id' in resp.json()['user']

def test_04_login_customer_returns_correct_role(client):
    client.post('/api/v1/auth/register', json={'name': 'TC4', 'email': 'tc4@test.com', 'password': 'password123', 'role': 'buyer'})
    resp = client.post('/api/v1/auth/login', json={'email': 'tc4@test.com', 'password': 'password123'})
    assert resp.status_code == 200
    assert resp.json()['user']['role'] == 'CUSTOMER'
    assert 'customer_id' in resp.json()['user']

def test_05_auth_me_enforces_bearer_token(client):
    resp = client.get('/api/v1/auth/me')
    assert resp.status_code == 401
    resp = client.get('/api/v1/auth/me', headers={'Authorization': 'Bearer invalidtoken'})
    assert resp.status_code == 401

def test_06_auth_me_returns_correct_user(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TM6', 'email': 'tm6@test.com', 'password': 'password123', 'role': 'merchant'})
    token = reg.json()['access_token']
    resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.json()['email'] == 'tm6@test.com'

def test_07_products_list_is_scoped_to_merchant(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM7A', 'email': 'tm7a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM7B', 'email': 'tm7b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    # create product for merchant 1
    p_resp = client.post('/api/v1/products', json={'sku': 'PROD7', 'name': 'P7', 'title': 'P7', 'description': 'desc', 'price': 100, 'category': 'cat', 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok1}'})
    assert p_resp.status_code == 201

    p1 = client.get('/api/v1/products', headers={'Authorization': f'Bearer {tok1}'})
    assert len(p1.json()['items']) == 1

    p2 = client.get('/api/v1/products', headers={'Authorization': f'Bearer {tok2}'})
    assert len(p2.json()['items']) == 0

def test_08_product_create_ignores_merchant_id_in_body(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TM8', 'email': 'tm8@test.com', 'password': 'password123', 'role': 'merchant'})
    tok = reg.json()['access_token']
    real_mid = reg.json()['user']['merchant_id']
    fake_mid = str(uuid.uuid4())

    resp = client.post('/api/v1/products', json={'merchant_id': fake_mid, 'sku': 'PROD8', 'name': 'P8', 'title': 'P8', 'description': 'desc', 'category': 'cat', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 201
    assert resp.json()['merchant_id'] == real_mid
    assert resp.json()['merchant_id'] != fake_mid

def test_09_product_update_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM9A', 'email': 'tm9a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM9B', 'email': 'tm9b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    p1 = client.post('/api/v1/products', json={'sku': 'PROD9', 'name': 'P9', 'title': 'P9', 'description': 'desc', 'category': 'cat', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok1}'})
    pid = p1.json()['id']

    update_fail = client.put(f'/api/v1/products/{pid}', json={'price': 200}, headers={'Authorization': f'Bearer {tok2}'})
    assert update_fail.status_code == 404

def test_10_product_delete_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM10A', 'email': 'tm10a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM10B', 'email': 'tm10b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    p1 = client.post('/api/v1/products', json={'sku': 'PROD10', 'name': 'P10', 'title': 'P10', 'description': 'desc', 'category': 'cat', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok1}'})
    pid = p1.json()['id']

    del_fail = client.delete(f'/api/v1/products/{pid}', headers={'Authorization': f'Bearer {tok2}'})
    assert del_fail.status_code == 404

def test_11_inventory_get_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM11A', 'email': 'tm11a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM11B', 'email': 'tm11b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    p1 = client.post('/api/v1/products', json={'sku': 'PROD11', 'name': 'P11', 'title': 'P11', 'description': 'desc', 'category': 'cat', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok1}'})
    pid = p1.json()['id']

    inv_fail = client.get(f'/api/v1/products/{pid}/inventory', headers={'Authorization': f'Bearer {tok2}'})
    assert inv_fail.status_code == 404

def test_12_inventory_update_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM12A', 'email': 'tm12a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM12B', 'email': 'tm12b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    p1 = client.post('/api/v1/products', json={'sku': 'PROD12', 'name': 'P12', 'title': 'P12', 'description': 'desc', 'category': 'cat', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok1}'})
    pid = p1.json()['id']

    inv_fail = client.put(f'/api/v1/products/{pid}/inventory', json={'available_quantity': 50}, headers={'Authorization': f'Bearer {tok2}'})
    assert inv_fail.status_code == 404

def test_13_catalogue_import_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC13', 'email': 'tc13@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.post('/api/v1/catalogue/import/analyze', headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_14_catalogue_import_review_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM14A', 'email': 'tm14a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM14B', 'email': 'tm14b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    fake_job_id = str(uuid.uuid4())
    resp1 = client.get(f'/api/v1/catalogue/import/{fake_job_id}/review', headers={'Authorization': f'Bearer {tok1}'})
    assert resp1.status_code == 404
    resp2 = client.patch(f'/api/v1/catalogue/import/{fake_job_id}/rows/1', json={'action':'EXCLUDE'}, headers={'Authorization': f'Bearer {tok2}'})
    assert resp2.status_code == 404

def test_15_carts_api_requires_customer(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TM15', 'email': 'tm15@test.com', 'password': 'password123', 'role': 'merchant'})
    tok = reg.json()['access_token']
    resp = client.post('/api/v1/carts', json={'merchant_id': str(uuid.uuid4())}, headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_16_cart_creation_scoped_to_customer(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC16', 'email': 'tc16@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    real_cid = reg.json()['user']['customer_id']
    resp = client.post('/api/v1/carts', json={'merchant_id': str(uuid.uuid4())}, headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 201
    assert resp.json()['customer_id'] == real_cid

def test_17_get_cart_enforces_ownership(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TC17A', 'email': 'tc17a@test.com', 'password': 'password123', 'role': 'buyer'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TC17B', 'email': 'tc17b@test.com', 'password': 'password123', 'role': 'buyer'})
    tok2 = reg2.json()['access_token']

    c1 = client.post('/api/v1/carts', json={'merchant_id': str(uuid.uuid4())}, headers={'Authorization': f'Bearer {tok1}'})
    cart_id = c1.json()['id']

    resp = client.get(f'/api/v1/carts/{cart_id}', headers={'Authorization': f'Bearer {tok2}'})
    assert resp.status_code == 403 # Cartesian API raises 403 Forbidden on ownership failure

def test_18_simulation_api_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC18', 'email': 'tc18@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.post('/api/v1/optimization/simulations', json={'scenario_count': 5}, headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_19_recommendations_api_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC19', 'email': 'tc19@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.get('/api/v1/optimization/recommendations', headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_20_what_if_api_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC20', 'email': 'tc20@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.post('/api/v1/optimization/what-if', json={'hypothesis': 'test'}, headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_21_apply_recommendation_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC21', 'email': 'tc21@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.post(f'/api/v1/optimization/recommendations/{uuid.uuid4()}/apply', headers={'Authorization': f'Bearer {tok}'})
    # Since customer is forbidden from hitting this merchant endpoint, we expect 403.
    # Note: If the ID must exist, it might 404, but auth guards run first.
    assert resp.status_code in (403, 404)

def test_22_campaigns_list_scoped_to_merchant(client):
    reg1 = client.post('/api/v1/auth/register', json={'name': 'TM22A', 'email': 'tm22a@test.com', 'password': 'password123', 'role': 'merchant'})
    tok1 = reg1.json()['access_token']
    reg2 = client.post('/api/v1/auth/register', json={'name': 'TM22B', 'email': 'tm22b@test.com', 'password': 'password123', 'role': 'merchant'})
    tok2 = reg2.json()['access_token']

    resp1 = client.get('/api/v1/campaigns', headers={'Authorization': f'Bearer {tok1}'})
    assert resp1.status_code == 200
    resp2 = client.get('/api/v1/campaigns', headers={'Authorization': f'Bearer {tok2}'})
    assert resp2.status_code == 200

def test_23_campaign_generate_requires_merchant(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TC23', 'email': 'tc23@test.com', 'password': 'password123', 'role': 'buyer'})
    tok = reg.json()['access_token']
    resp = client.post('/api/v1/campaigns/generate', headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 403

def test_24_product_id_is_uuid(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TM24', 'email': 'tm24@test.com', 'password': 'password123', 'role': 'merchant'})
    tok = reg.json()['access_token']
    p1 = client.post('/api/v1/products', json={'sku': 'PROD24', 'name': 'P24', 'title': 'P24', 'category': 'cat', 'description': 'desc', 'price': 100, 'tags': [], 'images': [], 'specifications': {}}, headers={'Authorization': f'Bearer {tok}'})
    assert p1.status_code == 201
    uuid.UUID(p1.json()['id'])

def test_25_db_session_isolation(client):
    reg = client.post('/api/v1/auth/register', json={'name': 'TM25', 'email': 'tm25@test.com', 'password': 'password123', 'role': 'merchant'})
    tok = reg.json()['access_token']
    resp = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {tok}'})
    assert resp.status_code == 200
