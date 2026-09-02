import sys
import os
sys.path.insert(0, '.')

import uuid
from app.core.database import SessionLocal
from app.services.optimization.recommendation_service import recommendation_service

def test_recommendation_generation():
    db = SessionLocal()
    merchant_id = uuid.UUID('e715fbe6-b364-4b99-a46d-f802ab164faf')
    run_id = uuid.uuid4()
    product_id = uuid.uuid4()

    events = [
        {"product_id": str(product_id), "reason": "MISSING_FEATURE", "count": 10},
        {"product_id": str(product_id), "reason": "DELIVERY_UNKNOWN", "count": 5},
        {"product_id": str(product_id), "reason": "DELIVERY_TOO_SLOW", "count": 3},
        {"product_id": str(product_id), "reason": "INVENTORY_ISSUE", "count": 15},
    ]

    recs = recommendation_service.generate_recommendations(db, merchant_id, events, run_id)
    
    print(f"Generated {len(recs)} recommendations:")
    for r in recs:
        print(f"[{r.type}] {r.title} (Count: {r.action_data.get('friction_count')})")
        print(f"  Reason: {r.reason}")
        print(f"  Action: {r.action_data.get('suggested_change')}\n")

    # Clean up test data
    for r in recs:
        db.delete(r)
    db.commit()
    db.close()

if __name__ == "__main__":
    test_recommendation_generation()
