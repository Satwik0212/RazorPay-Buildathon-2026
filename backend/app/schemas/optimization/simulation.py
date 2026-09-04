import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.schemas.buyer.intent import StructuredIntent


# Allowed scoring dimensions (must match ProductScorer.calculate_score keys)
VALID_WEIGHT_KEYS = {"quality", "metadata", "returns", "delivery", "price", "offers"}


class CustomBuyerConfig(BaseModel):
    """
    Merchant-defined custom AI buyer configuration.
    Resolved into the same internal representation as predefined persona weights + intent.
    Currency: max_budget is specified in RUPEES (₹) by the caller; the API layer
    converts to paise (minor units) before passing to the simulation engine.
    """
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Display name for this custom buyer (e.g. 'Weekend Audio Buyer')",
    )
    max_budget: Optional[int] = Field(
        default=None,
        ge=1,
        description="Maximum budget in RUPEES (e.g. 5000 = ₹5,000). Will be converted to paise internally.",
    )
    delivery_deadline_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Maximum acceptable delivery time in days.",
    )
    requirements: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Required product features/keywords (e.g. ['warranty', 'bluetooth']).",
    )
    weights: Dict[str, float] = Field(
        description=(
            "Scoring dimension weights. Keys must be from: quality, metadata, returns, delivery, price. "
            "Values must be non-negative and sum to exactly 1.0 (100%)."
        ),
    )
    scenario_count: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of simulation scenarios to run.",
    )

    @model_validator(mode="after")
    def validate_config(self) -> "CustomBuyerConfig":
        # 1. Clean requirements: strip and remove empty strings
        self.requirements = [
            r.strip() for r in self.requirements if r and r.strip()
        ]

        # 2. Validate weight keys
        unknown_keys = set(self.weights.keys()) - VALID_WEIGHT_KEYS
        if unknown_keys:
            raise ValueError(
                f"Unknown scoring dimensions: {unknown_keys}. "
                f"Valid keys are: {VALID_WEIGHT_KEYS}"
            )

        # 3. Validate non-negative weights
        for key, val in self.weights.items():
            if val < 0:
                raise ValueError(f"Weight '{key}' must be non-negative, got {val}.")

        # 4. Validate weights sum to 1.0 (±0.01 tolerance for float rounding)
        total = sum(self.weights.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Scoring weights must sum to 1.0 (100%), got {total:.4f}. "
                "Please adjust your weights so they total exactly 100%."
            )

        # 5. Normalise to exactly 1.0
        if self.weights:
            normalised = {k: v / total for k, v in self.weights.items()}
            self.weights = normalised

        return self


class SimulationCreate(BaseModel):
    merchant_id: Optional[uuid.UUID] = None
    scenario_count: int = Field(default=10, ge=1, le=100)
    buyer_profiles: List[str] = Field(default_factory=lambda: ["BUDGET", "QUALITY", "SPEED"])
    intent: Optional[StructuredIntent] = None
    # Custom buyer simulation: when present, predefined persona logic is bypassed.
    custom_buyer: Optional[CustomBuyerConfig] = None


class SimulationResultItem(BaseModel):
    persona_name: str
    selected_product_id: Optional[uuid.UUID] = None
    score: float
    constraints_satisfied: bool
    reason_codes: List[str] = []
    frictions: List[Dict[str, Any]] = []
    rankings: List[Dict[str, Any]] = []
    explanation: str = ""
    intent: Optional[Dict[str, Any]] = None
    persona_weights: Optional[Dict[str, float]] = None
    # Funnel counts: total products evaluated BEFORE truncation.
    # Allows frontend to show truthful numbers instead of sample-size counts.
    total_products_evaluated: Optional[int] = None
    total_eligible: Optional[int] = None
    total_disqualified: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class SimulationResponse(BaseModel):
    simulation_id: uuid.UUID
    merchant_id: uuid.UUID
    status: str
    scenario_count: int
    buyer_profiles: List[str]
    summary_metrics: Dict[str, Any] = {}
    results: List[SimulationResultItem] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

