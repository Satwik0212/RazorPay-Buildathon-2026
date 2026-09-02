import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.simulation import (
    SimulationCreate,
    SimulationResponse,
    SimulationResultItem,
)
from app.services.product_service import ProductService
from app.simulation.engine import simulation_engine
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant
from app.models.buyer_persona import BuyerPersona
from app.models.simulation_run import SimulationRun
from app.models.simulation_result import SimulationResult

router = APIRouter(prefix="/optimization", tags=["Optimization & Simulation"])

PERSONA_PROFILE_MAP = {
    "BUDGET": {"price": 0.50, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05},
    "SPEED": {"delivery": 0.55, "metadata": 0.20, "quality": 0.15, "price": 0.10},
    "QUALITY": {"quality": 0.50, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05},
    "FEATURE": {"metadata": 0.50, "quality": 0.25, "price": 0.15, "delivery": 0.10},
    "BALANCED": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05},
}


SCENARIO_VARIANTS = {
    "FEATURE": [
        ("feature_budget_low",    500000,   [],            None),
        ("feature_budget_mid",   1500000,   [],            None),
        ("feature_budget_high",  3000000,   [],            5),
        ("feature_deadline",     2000000,   [],            3),
        ("feature_premium",      5000000,   ["warranty"],  None),
    ],
    "BUDGET": [
        ("budget_tight",          300000,   [],            None),
        ("budget_moderate",       600000,   [],            None),
        ("budget_mid_quality",    800000,   ["warranty"],  None),
        ("budget_with_deadline",  500000,   [],            3),
        ("budget_high_value",    1000000,   [],            None),
    ],
    "SPEED": [
        ("speed_same_day",       2000000,   [],            1),
        ("speed_two_day",        1500000,   [],            2),
        ("speed_three_day",      2000000,   [],            3),
        ("speed_premium",        3000000,   ["warranty"],  1),
        ("speed_budget",          800000,   [],            2),
    ],
    "QUALITY": [
        ("quality_essentials",   1500000,   [],            None),
        ("quality_premium",      3000000,   ["warranty"],  None),
        ("quality_returns",      2000000,   [],            None),
        ("quality_complete",     4000000,   ["warranty"],  None),
        ("quality_balanced",     2500000,   [],            5),
    ],
    "BALANCED": [
        ("balanced_standard",    1000000,   [],            None),
        ("balanced_offers",      1500000,   [],            7),
        ("balanced_quality",     2000000,   ["warranty"],  None),
        ("balanced_speed",       1200000,   [],            3),
        ("balanced_premium",     3000000,   [],            None),
    ],
}


def _resolve_persona_weights(profile_name: str, db_personas: List[BuyerPersona]) -> Dict[str, float]:
    upper_name = profile_name.upper()
    if upper_name in PERSONA_PROFILE_MAP:
        return PERSONA_PROFILE_MAP[upper_name]

    # Search in DB personas
    for p in db_personas:
        if profile_name.lower() in p.name.lower():
            return p.weights

    return PERSONA_PROFILE_MAP["BALANCED"]


def _build_expanded_variant_pool(persona_key: str) -> List[tuple]:
    """
    Build an ordered list of (budget, requirements_tuple, deadline) triples for a persona.

    Phase 1 — Base variants (5 curated, distinct scenarios):
        The handcrafted SCENARIO_VARIANTS entries that reflect meaningful buyer archetypes.

    Phase 2 — Extended pool (Cartesian product of unique constraint dimensions):
        When a simulation requests MORE scenarios than the base variants cover, we
        deterministically generate additional unique buyer requirement combinations
        by taking the cross-product of:
          • every unique budget band found in the base variants
          • every unique requirements set  (e.g. [] or ['warranty'])
          • every unique deadline          (e.g. None, 3, 5)

        Combinations already present in Phase 1 are excluded, so there is zero overlap.
        The combined pool covers up to len(budgets) × len(reqs) × len(deadlines) unique
        buyer situations without inventing any new constraint semantics.

    All ordering is deterministic: sorted numerically/lexically so repeated calls
    always produce the same sequence.
    """
    from itertools import product as _product

    base_variants = SCENARIO_VARIANTS.get(persona_key.upper(), SCENARIO_VARIANTS["BALANCED"])

    # Extract unique constraint dimensions, preserving deterministic order
    budgets  = sorted(set(v[1] for v in base_variants))
    reqs_set = list(dict.fromkeys(tuple(v[2]) for v in base_variants))   # preserve insertion order, deduplicated
    deadlines = sorted(set(v[3] for v in base_variants), key=lambda x: (x is None, x or 0))

    # Phase 1: curated base pool as (budget, reqs_tuple, deadline)
    base_pool: List[tuple] = [(v[1], tuple(v[2]), v[3]) for v in base_variants]
    base_set = set(base_pool)

    # Phase 2: Cartesian product extended pool — excludes any tuple already in base_pool
    extended: List[tuple] = []
    for b, r, d in _product(budgets, reqs_set, deadlines):
        combo = (b, r, d)
        if combo not in base_set:
            extended.append(combo)

    return base_pool + extended


@router.post("/simulations", response_model=SimulationResponse, status_code=status.HTTP_200_OK)
def run_simulation(
    req: SimulationCreate,
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Executes synchronous, deterministic buyer simulations against the merchant's catalogue.
    Evaluates real buyer personas, applies hard/soft constraints, and detects friction.
    """
    merchant_id = current_merchant.id
    product_service = ProductService(db)
    db_products, _ = product_service.list_products(merchant_id=merchant_id, limit=100)

    # Convert DB products to dictionary catalogue format
    catalogue: List[Dict[str, Any]] = []
    for p in db_products:
        inv_qty = p.inventory.available_quantity if hasattr(p, "inventory") and p.inventory else 10
        catalogue.append({
            "id": p.id,
            "name": p.name,
            "description": p.description or "",
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "is_active": p.is_active,
            "product_metadata": p.product_metadata or {},
            "available_quantity": inv_qty,
        })

    # Fetch personas from DB
    db_personas = db.query(BuyerPersona).all()
    
    # If UI doesn't provide profiles, fallback to available DB personas or defaults
    if req.buyer_profiles:
        profiles = req.buyer_profiles
    else:
        profiles = [p.name.split(" ")[0].upper() for p in db_personas[:4]]
        if not profiles:
            profiles = ["BUDGET", "SPEED", "QUALITY", "BALANCED"]

    sim_id = uuid.uuid4()
    results: List[SimulationResultItem] = []
    friction_summary: Dict[str, int] = {}
    detailed_frictions: List[Dict[str, Any]] = []
    persona_success_count: Dict[str, int] = {}
    
    db_results = []

    # Pre-build the expanded variant pool for every distinct selected persona.
    # Each persona's pool starts with its 5 curated base variants, then continues
    # with additional deterministic combinations of the same constraint dimensions
    # (budget × requirements × deadline). This ensures that even with 1 or 2 personas
    # selected, a 20-scenario run draws from ≥20 distinct buyer configurations.
    from collections import defaultdict
    _profile_pools: Dict[str, List[tuple]] = {
        p.upper(): _build_expanded_variant_pool(p)
        for p in set(profiles)
    }
    _profile_variant_counters: Dict[str, int] = defaultdict(int)

    # Also pre-index the base labels for readable persona names on base variants
    _base_labels: Dict[str, List[str]] = {
        p.upper(): [v[0] for v in SCENARIO_VARIANTS.get(p.upper(), SCENARIO_VARIANTS["BALANCED"])]
        for p in set(profiles)
    }

    # Run simulation iterations
    for index in range(req.scenario_count):
        base_profile_name = profiles[index % len(profiles)]
        weights = _resolve_persona_weights(base_profile_name, db_personas)

        if req.intent:
            intent_dict = req.intent.model_dump()
            variant_label = f"explicit_{index + 1}"
        else:
            pool = _profile_pools[base_profile_name.upper()]
            base_labels = _base_labels[base_profile_name.upper()]
            n_base = len(base_labels)

            variant_index = _profile_variant_counters[base_profile_name] % len(pool)
            _profile_variant_counters[base_profile_name] += 1

            max_budget, requirements, deadline = pool[variant_index]

            # Use the curated label for the first N base variants; generate a
            # deterministic label for extended combinations so the name reflects
            # the actual constraint values and is unique.
            if variant_index < n_base:
                variant_label = base_labels[variant_index]
            else:
                # e.g. "ext_b1500000_r1_d3" — budget + requirements flag + deadline
                req_flag = "1" if requirements else "0"
                dl_str = str(deadline) if deadline is not None else "x"
                variant_label = f"ext_b{max_budget}_r{req_flag}_d{dl_str}"

            intent_dict = {"max_budget": max_budget, "requirements": list(requirements)}
            if deadline is not None:
                intent_dict["delivery_deadline_days"] = deadline

        full_persona_name = f"{base_profile_name}:{variant_label}"


        sim_output = simulation_engine.run_simulation(
            merchant_id=str(merchant_id),
            persona_weights=weights,
            intent=intent_dict,
            catalogue=catalogue,
            persona_name=full_persona_name,
        )

        selected_id = uuid.UUID(sim_output["selected_product_id"]) if sim_output["selected_product_id"] else None

        # Track friction summary
        for f in sim_output.get("frictions", []):
            reason_name = f.get("reason", "UNKNOWN")
            friction_summary[reason_name] = friction_summary.get(reason_name, 0) + 1
            detailed_frictions.append({
                "product_id": f.get("product_id"),
                "reason": reason_name,
                "count": 1
            })

        # Track persona success
        if sim_output["constraints_satisfied"]:
            persona_success_count[full_persona_name] = persona_success_count.get(full_persona_name, 0) + 1

        result_item = SimulationResultItem(
            persona_name=full_persona_name,
            selected_product_id=selected_id,
            score=sim_output["score"],
            constraints_satisfied=sim_output["constraints_satisfied"],
            reason_codes=sim_output["reason_codes"],
            frictions=sim_output["frictions"],
            rankings=sim_output["rankings"],
            explanation=sim_output["explanation"],
            intent=intent_dict,
            persona_weights=weights,
        )
        results.append(result_item)
        
        db_results.append(SimulationResult(
            id=uuid.uuid4(),
            persona_name=full_persona_name,
            selected_product_id=selected_id,
            score=sim_output["score"],
            constraints_satisfied=sim_output["constraints_satisfied"],
            reason_codes=sim_output["reason_codes"],
            frictions=sim_output["frictions"],
            rankings=sim_output["rankings"],
            explanation=sim_output["explanation"],
        ))

    # Compute comprehensive summary metrics
    total_simulated = len(results)
    successful_matches = sum(1 for r in results if r.constraints_satisfied and r.selected_product_id is not None)
    failed_matches = total_simulated - successful_matches
    satisfaction_rate = round(successful_matches / max(total_simulated, 1), 3)
    avg_score = round(sum(r.score for r in results) / max(total_simulated, 1), 3)

    summary_metrics = {
        "buyers_simulated": total_simulated,
        "successful_matches": successful_matches,
        "failed_matches": failed_matches,
        "constraint_satisfaction_rate": satisfaction_rate,
        "average_score": avg_score,
        "friction_distribution": friction_summary,
        "persona_success_rates": {
            p: round(persona_success_count.get(p, 0) / max(sum(1 for r in results if r.persona_name == p), 1), 2)
            for p in set(r.persona_name for r in results)
        },
        "metric_type": "SIMULATED RESULT",
    }
    
    # Persist the SimulationRun and SimulationResult records
    sim_run = SimulationRun(
        id=sim_id,
        merchant_id=merchant_id,
        status="COMPLETED",
        scenario_count=total_simulated,
        buyer_profiles=profiles,
        summary_metrics=summary_metrics,
        results=db_results
    )
    db.add(sim_run)
    db.commit()

    # Persist the collected friction evidence as actionable recommendations
    if detailed_frictions:
        from app.services.optimization.recommendation_service import recommendation_service
        recommendation_service.generate_recommendations(db, merchant_id, detailed_frictions, simulation_run_id=sim_id, scenario_count=total_simulated)

    return SimulationResponse(
        simulation_id=sim_id,
        merchant_id=merchant_id,
        status="COMPLETED",
        scenario_count=total_simulated,
        buyer_profiles=profiles,
        summary_metrics=summary_metrics,
        results=results,
        created_at=datetime.now(timezone.utc),
    )

