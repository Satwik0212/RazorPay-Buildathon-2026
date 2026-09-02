"""
Startup seed for canonical buyer personas.

Seeds the 5 canonical synthetic buyer personas that mirror the
PERSONA_PROFILE_MAP used by the simulation engine.  Runs
idempotently on every application start: if a persona with a given
name already exists it is skipped, so re-runs are safe.
"""

import logging
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.buyer_persona import BuyerPersona

logger = logging.getLogger(__name__)

# These weights mirror PERSONA_PROFILE_MAP in
# app/api/v1/optimization/simulations.py.  Keep them in sync.
CANONICAL_PERSONAS = [
    {
        "name": "Budget Conscious Buyer",
        "description": (
            "Highly price-sensitive persona that prioritises the lowest cost "
            "option. Will accept slower delivery and fewer features if it means "
            "a lower price. Discount offers and deals are a strong attractor."
        ),
        "budget_min": 0,
        "budget_max": 500_000,       # 5 000 INR in paise
        "priorities": ["price", "offers", "discount"],
        "urgency": "LOW",
        "weights": {
            "price": 0.50,
            "offers": 0.25,
            "delivery": 0.10,
            "quality": 0.10,
            "returns": 0.05,
        },
    },
    {
        "name": "Speed Priority Buyer",
        "description": (
            "Urgency-driven persona that demands the fastest possible delivery. "
            "Willing to pay a premium for speed. Considers fast shipping a "
            "hard requirement; missing delivery metadata is a strong friction signal."
        ),
        "budget_min": 0,
        "budget_max": 1_000_000,     # 10 000 INR
        "priorities": ["delivery", "availability", "fast_shipping"],
        "urgency": "CRITICAL",
        "weights": {
            "delivery": 0.55,
            "metadata": 0.20,
            "quality": 0.15,
            "price": 0.10,
        },
    },
    {
        "name": "Quality Seeker Buyer",
        "description": (
            "Premium-oriented persona that values product quality and brand "
            "reputation above all else. Expects detailed specifications, "
            "warranty information, and hassle-free returns."
        ),
        "budget_min": 0,
        "budget_max": 2_000_000,     # 20 000 INR
        "priorities": ["quality", "warranty", "brand", "returns"],
        "urgency": "MEDIUM",
        "weights": {
            "quality": 0.50,
            "metadata": 0.20,
            "returns": 0.15,
            "delivery": 0.10,
            "price": 0.05,
        },
    },
    {
        "name": "Feature Researcher Buyer",
        "description": (
            "Detail-obsessed persona that reads every specification before "
            "purchasing. Rich metadata (specs, tech details, comparisons) "
            "drives purchase decisions. Sparse listings cause friction."
        ),
        "budget_min": 0,
        "budget_max": 1_500_000,     # 15 000 INR
        "priorities": ["specifications", "metadata", "reviews", "comparisons"],
        "urgency": "LOW",
        "weights": {
            "metadata": 0.50,
            "quality": 0.25,
            "price": 0.15,
            "delivery": 0.10,
        },
    },
    {
        "name": "Balanced Pragmatic Buyer",
        "description": (
            "Well-rounded persona that evaluates products across all dimensions "
            "without strong bias. Represents the median buyer and provides a "
            "useful baseline for overall catalogue health."
        ),
        "budget_min": 0,
        "budget_max": 1_000_000,     # 10 000 INR
        "priorities": ["price", "quality", "delivery", "returns"],
        "urgency": "MEDIUM",
        "weights": {
            "price": 0.25,
            "quality": 0.25,
            "delivery": 0.20,
            "returns": 0.15,
            "offers": 0.10,
            "metadata": 0.05,
        },
    },
]


def seed_buyer_personas() -> None:
    """
    Idempotently seed the canonical buyer personas into the database.
    Called once during application startup after schema initialisation.
    """
    db: Session = SessionLocal()
    try:
        created = 0
        skipped = 0
        for persona_data in CANONICAL_PERSONAS:
            existing = (
                db.query(BuyerPersona)
                .filter(BuyerPersona.name == persona_data["name"])
                .first()
            )
            if existing:
                skipped += 1
                continue

            persona = BuyerPersona(
                name=persona_data["name"],
                description=persona_data["description"],
                budget_min=persona_data["budget_min"],
                budget_max=persona_data["budget_max"],
                priorities=persona_data["priorities"],
                urgency=persona_data["urgency"],
                weights=persona_data["weights"],
            )
            db.add(persona)
            created += 1

        db.commit()
        logger.info(
            "Buyer persona seed complete: %d created, %d already present.",
            created,
            skipped,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Failed to seed buyer personas: %s", exc, exc_info=True)
    finally:
        db.close()
