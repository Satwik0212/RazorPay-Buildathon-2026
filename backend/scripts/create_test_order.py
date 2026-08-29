import requests
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from app.core.config import settings
    rzp_key_id = settings.RAZORPAY_KEY_ID
except ImportError:
    print("Warning: Could not import settings, falling back to environment variable")
    rzp_key_id = os.environ.get("RAZORPAY_KEY_ID")

if not rzp_key_id:
    print("Error: RAZORPAY_KEY_ID not found in environment or settings.")
    sys.exit(1)

BASE_URL = "http://localhost:8000/api/v1"

print("1. Logging in as buyer...")
resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "buyer@demo.com", "password": "password123"})
if resp.status_code != 200:
    print(f"Login failed: {resp.text}")
    sys.exit(1)
token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("1.5. Updating Merchant Policy...")
m_resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "merchant@demo.com", "password": "password123"})
m_token = m_resp.json()["access_token"]
pol_resp = requests.put(f"{BASE_URL}/merchant/policy", json={
    "max_autonomous_amount": 5000000000,
    "daily_autonomous_limit": 10000000000,
    "require_approval_above": 2000000000,
    "blocked_categories": ["gambling", "restricted"],
    "is_ai_enabled": True
}, headers={"Authorization": f"Bearer {m_token}"})
if pol_resp.status_code != 200:
    print("Policy update failed", pol_resp.text)
    sys.exit(1)

print("2. Fetching products...")
products_resp = requests.get(f"{BASE_URL}/catalog/", headers=headers).json()
items = products_resp["items"] if "items" in products_resp else products_resp
product = min(items, key=lambda x: x['price'])
product_id = product["id"]
merchant_id = product["merchant_id"]

print(f"3. Creating cart for merchant {merchant_id}...")
cart_resp = requests.post(f"{BASE_URL}/carts", json={"merchant_id": merchant_id}, headers=headers)
if cart_resp.status_code != 201 and cart_resp.status_code != 200:
    print(cart_resp.text)
    sys.exit(1)
cart = cart_resp.json()
requests.post(f"{BASE_URL}/carts/{cart['id']}/items", json={"product_id": product_id, "quantity": 1}, headers=headers)

print("4. Generating Quote...")
quote_resp = requests.post(f"{BASE_URL}/quotes", json={"cart_id": cart['id']}, headers=headers)
if quote_resp.status_code != 201 and quote_resp.status_code != 200:
    print(quote_resp.text)
    sys.exit(1)
quote = quote_resp.json()

print("5. Authorizing Quote & Creating Order...")
auth_resp = requests.post(f"{BASE_URL}/authorizations", json={"quote_id": quote['quote_id']}, headers=headers)
if auth_resp.status_code != 201 and auth_resp.status_code != 200:
    print("Auth failed:")
    print(auth_resp.text)
    sys.exit(1)
auth = auth_resp.json()

order_resp = requests.post(f"{BASE_URL}/checkout/orders", json={"quote_id": quote['quote_id'], "authorization_id": auth['authorization_id']}, headers=headers)
if order_resp.status_code != 201 and order_resp.status_code != 200:
    print("Order failed:")
    print(order_resp.text)
    sys.exit(1)
order = order_resp.json()

if 'razorpay_order_id' not in order:
    print(f"Failed to create razorpay order: {order}")
    sys.exit(1)

rzp_order_id = order['razorpay_order_id']
amount = order['amount']
currency = "INR"

html = f"""
<html>
<head><title>Razorpay Test Checkout</title></head>
<body style="font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh;">
    <h1>Webhook Smoke Test Checkout</h1>
    <p>Order ID: {rzp_order_id}</p>
    <p>Amount: {amount / 100} INR</p>
    <button id="rzp-button1" style="padding: 10px 20px; font-size: 16px; background: #3399cc; color: white; border: none; border-radius: 4px; cursor: pointer;">
        Pay with Razorpay
    </button>
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
<script>
var options = {{
    "key": "{rzp_key_id}", 
    "amount": "{amount}", 
    "currency": "{currency}",
    "name": "Razorpay Buildathon Demo",
    "order_id": "{rzp_order_id}",
    "handler": function (response){{
        alert("Payment Successful! Razorpay has now sent the webhook to the Cloudflare tunnel.");
        document.body.innerHTML += "<br><br><b>Payment Success! You can now check the backend logs.</b>";
    }}
}};
var rzp1 = new Razorpay(options);
document.getElementById('rzp-button1').onclick = function(e){{
    rzp1.open();
    e.preventDefault();
}}
</script>
</body>
</html>
"""
with open("checkout.html", "w") as f:
    f.write(html)

print(f"\n[SUCCESS] Created real Razorpay order: {rzp_order_id}")
print("[SUCCESS] Wrote checkout.html. Open this file in your browser to trigger payment and the webhook!")
