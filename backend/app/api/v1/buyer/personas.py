import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.buyer.persona import BuyerPersonaCreate, BuyerPersonaResponse

router = APIRouter(prefix="/buyer-personas", tags=["Buyer Personas"])

DEFAULT_PERSONAS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Budget Conscious Buyer",
        "description": "Prioritizes discount and lower overall price over speed.",
        "budget_min": 50000,
        "budget_max": 300000,
        "priorities": ["price", "discount"],
        "urgency": "LOW",
        "weights": {"price": 0.5, "discount": 0.3, "speed": 0.1, "quality": 0.1},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Speed First Buyer",
        "description": "Requires fast delivery deadlines and immediate stock availability.",
        "budget_min": 100000,
        "budget_max": 800000,
        "priorities": ["delivery", "stock"],
        "urgency": "HIGH",
        "weights": {"delivery": 0.5, "stock": 0.3, "price": 0.1, "quality": 0.1},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
]


@router.get("", response_model=List[BuyerPersonaResponse])
def list_buyer_personas():
    return [BuyerPersonaResponse(**p) for p in DEFAULT_PERSONAS]
