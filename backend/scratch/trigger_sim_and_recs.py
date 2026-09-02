import requests
import json
import sys
sys.path.insert(0, '.')

# Login
login_res = requests.post('http://127.0.0.1:8000/api/v1/auth/login', json={
    'email': 'merchant@demo.com',
    'password': 'password123'
})
token = login_res.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Run simulation
print("Running simulation...")
sim_res = requests.post('http://127.0.0.1:8000/api/v1/optimization/simulations', headers=headers, json={
    "scenario_count": 20,
    "buyer_profiles": ["FEATURE", "BUDGET", "QUALITY", "SPEED", "BALANCED"]
})
sim_data = sim_res.json()
print("Simulation complete. ID:", sim_data.get('simulation_id'))

from app.core.database import SessionLocal
from app.models.optimization_recommendation import OptimizationRecommendation

print("Fetching from database...")
db = SessionLocal()
recs = db.query(OptimizationRecommendation).all()
print(f"Total recommendations in DB: {len(recs)}")

types_seen = set()
for r in recs:
    types_seen.add(r.type)

print("Types found:", types_seen)

for type_to_print in types_seen:
    r = next(item for item in recs if item.type == type_to_print)
    print(f"\n--- Example: {r.type} ---")
    print(f"Title: {r.title}")
    print(f"Reason: {r.reason}")
    print(f"Action: {r.action_data.get('suggested_change')}")
    print(f"Count: {r.action_data.get('friction_count')}")
db.close()

