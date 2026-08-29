import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.schemas.buyer.persona import BuyerPersonaCreate, BuyerPersonaResponse

router = APIRouter(prefix="/buyer-personas", tags=["Buyer Personas"])

DEFAULT_PERSONAS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "name": "Budget Conscious Buyer",
        "description": "Prioritizes discount, affordability, and lower overall price over speed.",
        "budget_min": 10000,
        "budget_max": 500000,
        "priorities": ["price", "discount", "offers"],
        "urgency": "LOW",
        "weights": {"price": 0.45, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05, "metadata": 0.05},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000002"),
        "name": "Speed First Buyer",
        "description": "Requires fast delivery deadlines and immediate stock availability.",
        "budget_min": 50000,
        "budget_max": 1000000,
        "priorities": ["delivery", "stock", "speed"],
        "urgency": "HIGH",
        "weights": {"delivery": 0.50, "metadata": 0.20, "quality": 0.15, "price": 0.10, "returns": 0.05, "offers": 0.00},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000003"),
        "name": "Quality & Brand Focused Buyer",
        "description": "Prioritizes high build quality, return policies, and high ratings over discounts.",
        "budget_min": 100000,
        "budget_max": 2000000,
        "priorities": ["quality", "warranty", "returns"],
        "urgency": "MEDIUM",
        "weights": {"quality": 0.45, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05, "offers": 0.05},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000004"),
        "name": "Feature & Specification Focused",
        "description": "Scrutinizes technical attributes, explicit requirements, and rich product metadata.",
        "budget_min": 50000,
        "budget_max": 1500000,
        "priorities": ["metadata", "specifications", "features"],
        "urgency": "MEDIUM",
        "weights": {"metadata": 0.45, "quality": 0.25, "price": 0.15, "delivery": 0.10, "returns": 0.05, "offers": 0.00},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000005"),
        "name": "Balanced Buyer",
        "description": "Evaluates a balanced trade-off across price, quality, delivery, and return clarity.",
        "budget_min": 25000,
        "budget_max": 1000000,
        "priorities": ["balanced"],
        "urgency": "MEDIUM",
        "weights": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    },
]

# Memory registry for dynamically registered personas during session
_custom_personas = []


@router.get("", response_model=List[BuyerPersonaResponse])
def list_buyer_personas():
    """
    List all synthetic buyer personas.
    """
    all_personas = DEFAULT_PERSONAS + _custom_personas
    return [BuyerPersonaResponse(**p) for p in all_personas]


@router.post("", response_model=BuyerPersonaResponse, status_code=status.HTTP_201_CREATED)
def create_buyer_persona(req: BuyerPersonaCreate):
    """
    Create a new custom buyer persona with validated scoring weights.
    """
    if req.weights:
        total_weight = sum(req.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Persona weights must sum to 1.0, current sum is {total_weight:.3f}",
            )

    new_persona = {
        "id": uuid.uuid4(),
        "name": req.name,
        "description": req.description,
        "budget_min": req.budget_min,
        "budget_max": req.budget_max,
        "priorities": req.priorities,
        "urgency": req.urgency,
        "weights": req.weights,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    _custom_personas.append(new_persona)
    return BuyerPersonaResponse(**new_persona)
