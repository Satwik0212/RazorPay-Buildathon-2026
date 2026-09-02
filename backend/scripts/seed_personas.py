import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.buyer_persona import BuyerPersona

DEFAULT_PERSONAS = [
    {
        "name": "Budget Conscious Buyer",
        "description": "Prioritizes discount, affordability, and lower overall price over speed.",
        "budget_min": 10000,
        "budget_max": 500000,
        "priorities": ["price", "discount", "offers"],
        "urgency": "LOW",
        "weights": {"price": 0.45, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05, "metadata": 0.05},
    },
    {
        "name": "Speed First Buyer",
        "description": "Requires fast delivery deadlines and immediate stock availability.",
        "budget_min": 50000,
        "budget_max": 1000000,
        "priorities": ["delivery", "stock", "speed"],
        "urgency": "HIGH",
        "weights": {"delivery": 0.50, "metadata": 0.20, "quality": 0.15, "price": 0.10, "returns": 0.05, "offers": 0.00},
    },
    {
        "name": "Quality & Brand Focused Buyer",
        "description": "Prioritizes high build quality, return policies, and high ratings over discounts.",
        "budget_min": 100000,
        "budget_max": 2000000,
        "priorities": ["quality", "warranty", "returns"],
        "urgency": "MEDIUM",
        "weights": {"quality": 0.45, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05, "offers": 0.05},
    },
    {
        "name": "Feature & Specification Focused",
        "description": "Scrutinizes technical attributes, explicit requirements, and rich product metadata.",
        "budget_min": 50000,
        "budget_max": 1500000,
        "priorities": ["metadata", "specifications", "features"],
        "urgency": "MEDIUM",
        "weights": {"metadata": 0.45, "quality": 0.25, "price": 0.15, "delivery": 0.10, "returns": 0.05, "offers": 0.00},
    },
    {
        "name": "Balanced Buyer",
        "description": "Evaluates a balanced trade-off across price, quality, delivery, and return clarity.",
        "budget_min": 25000,
        "budget_max": 1000000,
        "priorities": ["balanced"],
        "urgency": "MEDIUM",
        "weights": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05},
    },
]

def seed_personas():
    db = SessionLocal()
    try:
        print("Seeding default buyer personas...")
        count = 0
        for p_data in DEFAULT_PERSONAS:
            existing = db.query(BuyerPersona).filter(BuyerPersona.name == p_data["name"]).first()
            if not existing:
                persona = BuyerPersona(**p_data)
                db.add(persona)
                count += 1
        
        db.commit()
        print(f"Successfully seeded {count} new buyer personas.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding personas: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_personas()
