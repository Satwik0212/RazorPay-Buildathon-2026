import uuid
from typing import Dict, Any, List, Optional
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


SCENARIO_WEIGHT_OVERRIDES: Dict[str, Dict[str, float]] = {
    # QUALITY scenario-specific weight profiles (normalized to 1.00)
    "quality_essentials": {
        "quality": 0.50,
        "metadata": 0.20,
        "returns": 0.15,
        "delivery": 0.10,
        "price": 0.05,
    },
    "quality_premium": {
        "quality": 0.55,
        "metadata": 0.25,
        "returns": 0.10,
        "delivery": 0.05,
        "price": 0.05,
    },
    "quality_returns": {
        "returns": 0.40,
        "quality": 0.30,
        "metadata": 0.15,
        "delivery": 0.10,
        "price": 0.05,
    },
    "quality_complete": {
        "metadata": 0.45,
        "quality": 0.35,
        "returns": 0.10,
        "delivery": 0.05,
        "price": 0.05,
    },
    "quality_balanced": {
        "quality": 0.30,
        "price": 0.25,
        "metadata": 0.20,
        "delivery": 0.15,
        "returns": 0.10,
    },
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


def truncate_rankings(
    rankings: List[Dict[str, Any]],
    selected_product_id: Optional[Any],
    max_passed: int = 20,
    max_disqualified: int = 10,
) -> List[Dict[str, Any]]:
    passed = [r for r in rankings if r.get("passed") is True]
    disqualified = [r for r in rankings if r.get("passed") is False]

    truncated_passed = passed[:max_passed]
    truncated_disqualified = disqualified[:max_disqualified]

    selected_id_str = str(selected_product_id) if selected_product_id else None
    if selected_id_str:
        winner_in_passed = any(str(r.get("product_id")) == selected_id_str for r in truncated_passed)
        if not winner_in_passed:
            winner_item = next((r for r in passed[max_passed:] if str(r.get("product_id")) == selected_id_str), None)
            if winner_item:
                truncated_passed.append(winner_item)

    return truncated_passed + truncated_disqualified


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
    # 1. Retrieve all active products for the authenticated merchant
    merchant_id = current_merchant.id
    product_service = ProductService(db)
    catalogue = product_service.get_active_catalogue(merchant_id=merchant_id)

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
    friction_summary: Dict[str, int] = {}
    detailed_frictions: List[Dict[str, Any]] = []
    persona_success_count: Dict[str, int] = {}
    evaluations: List[Dict[str, Any]] = []

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

    # 2. Route: Custom Buyer Simulation
    # When req.custom_buyer is provided, bypass predefined persona/variant logic entirely.
    # The existing simulation_engine.run_simulation(), ProductScorer, and FrictionDetector
    # are used unchanged — only the weights and intent are merchant-specified.
    if req.custom_buyer:
        custom = req.custom_buyer

        # Convert budget from Rupees (merchant-entered) to paise (engine currency)
        max_budget_paise = custom.max_budget * 100 if custom.max_budget is not None else None

        # Build intent dict matching the shape expected by FrictionDetector
        custom_intent: Dict[str, Any] = {
            "requirements": custom.requirements,
        }
        if max_budget_paise is not None:
            custom_intent["max_budget"] = max_budget_paise
        if custom.delivery_deadline_days is not None:
            custom_intent["delivery_deadline_days"] = custom.delivery_deadline_days

        # Use the merchant-specified weights directly (already normalised in schema)
        custom_weights = dict(custom.weights)

        sim_id = uuid.uuid4()
        friction_summary: Dict[str, int] = {}
        detailed_frictions: List[Dict[str, Any]] = []
        persona_success_count: Dict[str, int] = {}
        evaluations: List[Dict[str, Any]] = []

        scenario_count = custom.scenario_count if custom.scenario_count else req.scenario_count

        for i in range(scenario_count):
            # For multiple runs the persona_name includes the run index for traceability
            if scenario_count > 1:
                persona_name = f"CUSTOM:{custom.name}:run_{i + 1}"
            else:
                persona_name = f"CUSTOM:{custom.name}"

            sim_output = simulation_engine.run_simulation(
                merchant_id=str(merchant_id),
                persona_weights=custom_weights,
                intent=custom_intent,
                catalogue=catalogue,
                persona_name=persona_name,
            )

            selected_id = (
                uuid.UUID(sim_output["selected_product_id"])
                if sim_output["selected_product_id"]
                else None
            )

            for f in sim_output.get("frictions", []):
                reason_name = f.get("reason", "UNKNOWN")
                friction_summary[reason_name] = friction_summary.get(reason_name, 0) + 1
                det_f = {
                    "product_id": f.get("product_id"),
                    "reason": reason_name,
                    "count": 1,
                }
                if "delivery_deadline_days" in f:
                    det_f["delivery_deadline_days"] = f["delivery_deadline_days"]
                detailed_frictions.append(det_f)

            if sim_output["constraints_satisfied"]:
                persona_success_count[persona_name] = (
                    persona_success_count.get(persona_name, 0) + 1
                )

            evaluations.append({
                "full_persona_name": persona_name,
                "selected_id": selected_id,
                "weights": custom_weights,
                "intent_dict": custom_intent,
                "sim_output": sim_output,
            })

        # Summary metrics — identical structure to predefined path
        total_simulated = len(evaluations)
        successful_matches = sum(
            1 for e in evaluations
            if e["sim_output"]["constraints_satisfied"] and e["selected_id"] is not None
        )
        failed_matches = total_simulated - successful_matches
        satisfaction_rate = round(successful_matches / max(total_simulated, 1), 3)
        avg_score = round(
            sum(e["sim_output"]["score"] for e in evaluations) / max(total_simulated, 1), 3
        )

        summary_metrics = {
            "buyers_simulated": total_simulated,
            "successful_matches": successful_matches,
            "failed_matches": failed_matches,
            "constraint_satisfaction_rate": satisfaction_rate,
            "average_score": avg_score,
            "friction_distribution": friction_summary,
            "persona_success_rates": {
                p: round(
                    persona_success_count.get(p, 0)
                    / max(sum(1 for e in evaluations if e["full_persona_name"] == p), 1),
                    2,
                )
                for p in set(e["full_persona_name"] for e in evaluations)
            },
            "metric_type": "CUSTOM SIMULATION",
            "custom_buyer_name": custom.name,
        }

        results: List[SimulationResultItem] = []
        db_results = []

        for ev in evaluations:
            sim_out = ev["sim_output"]
            sel_id = ev["selected_id"]
            pname = ev["full_persona_name"]
            w = ev["weights"]
            idict = ev["intent_dict"]

            full_rankings = sim_out["rankings"]
            total_evaluated = len(full_rankings)
            total_eligible_count = sum(1 for r in full_rankings if r.get("passed") is True)
            total_disqualified_count = sum(1 for r in full_rankings if r.get("passed") is False)

            truncated_rankings = truncate_rankings(
                rankings=full_rankings,
                selected_product_id=sel_id,
                max_passed=20,
                max_disqualified=10,
            )

            results.append(SimulationResultItem(
                persona_name=pname,
                selected_product_id=sel_id,
                score=sim_out["score"],
                constraints_satisfied=sim_out["constraints_satisfied"],
                reason_codes=sim_out["reason_codes"],
                frictions=sim_out["frictions"],
                rankings=truncated_rankings,
                explanation=sim_out["explanation"],
                intent=idict,
                persona_weights=w,
                total_products_evaluated=total_evaluated,
                total_eligible=total_eligible_count,
                total_disqualified=total_disqualified_count,
                score_breakdown=sim_out.get("score_breakdown"),
                selected_product_name=sim_out.get("selected_product_name"),
                selected_product_price=sim_out.get("selected_product_price"),
                selected_product_category=sim_out.get("selected_product_category"),
            ))

            db_results.append(SimulationResult(
                id=uuid.uuid4(),
                persona_name=pname,
                selected_product_id=sel_id,
                score=sim_out["score"],
                constraints_satisfied=sim_out["constraints_satisfied"],
                reason_codes=sim_out["reason_codes"],
                frictions=sim_out["frictions"],
                rankings=truncated_rankings,
                explanation=sim_out["explanation"],
            ))

        buyer_profiles_label = [f"CUSTOM:{custom.name}"]

        sim_run = SimulationRun(
            id=sim_id,
            merchant_id=merchant_id,
            status="COMPLETED",
            scenario_count=total_simulated,
            buyer_profiles=buyer_profiles_label,
            summary_metrics=summary_metrics,
            results=db_results,
        )
        db.add(sim_run)
        db.commit()

        if detailed_frictions:
            from app.services.optimization.recommendation_service import recommendation_service
            recommendation_service.generate_recommendations(
                db,
                merchant_id,
                detailed_frictions,
                simulation_run_id=sim_id,
                scenario_count=total_simulated,
            )

        return SimulationResponse(
            simulation_id=sim_id,
            merchant_id=merchant_id,
            status="COMPLETED",
            scenario_count=total_simulated,
            buyer_profiles=buyer_profiles_label,
            summary_metrics=summary_metrics,
            results=results,
            created_at=datetime.now(timezone.utc),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Route: Predefined Persona Simulation (original logic, unchanged)
    # ─────────────────────────────────────────────────────────────────────────
    # If UI doesn't provide profiles, fallback to available DB personas or defaults

    # Detect hard constraints, soft friction, calculate scores, deterministic tie-breaking, select winners
    for index in range(req.scenario_count):
        base_profile_name = profiles[index % len(profiles)]
        base_weights = _resolve_persona_weights(base_profile_name, db_personas)

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

        # Resolve scenario-specific weights without mutating global persona profiles
        weights = dict(base_weights)
        if variant_label in SCENARIO_WEIGHT_OVERRIDES:
            weights = dict(SCENARIO_WEIGHT_OVERRIDES[variant_label])

        sim_output = simulation_engine.run_simulation(
            merchant_id=str(merchant_id),
            persona_weights=weights,
            intent=intent_dict,
            catalogue=catalogue,
            persona_name=full_persona_name,
        )

        selected_id = uuid.UUID(sim_output["selected_product_id"]) if sim_output["selected_product_id"] else None

        # Track friction summary & detailed frictions across 100% of candidate evaluations
        for f in sim_output.get("frictions", []):
            reason_name = f.get("reason", "UNKNOWN")
            friction_summary[reason_name] = friction_summary.get(reason_name, 0) + 1
            det_f = {
                "product_id": f.get("product_id"),
                "reason": reason_name,
                "count": 1
            }
            if "delivery_deadline_days" in f:
                det_f["delivery_deadline_days"] = f["delivery_deadline_days"]
            detailed_frictions.append(det_f)

        # Track persona success
        if sim_output["constraints_satisfied"]:
            persona_success_count[full_persona_name] = persona_success_count.get(full_persona_name, 0) + 1

        evaluations.append({
            "full_persona_name": full_persona_name,
            "selected_id": selected_id,
            "weights": weights,
            "intent_dict": intent_dict,
            "sim_output": sim_output,
        })

    # 4. Generate summary metrics and recommendation evidence across 100% of candidate evaluation results
    total_simulated = len(evaluations)
    successful_matches = sum(
        1 for e in evaluations
        if e["sim_output"]["constraints_satisfied"] and e["selected_id"] is not None
    )
    failed_matches = total_simulated - successful_matches
    satisfaction_rate = round(successful_matches / max(total_simulated, 1), 3)
    avg_score = round(sum(e["sim_output"]["score"] for e in evaluations) / max(total_simulated, 1), 3)

    summary_metrics = {
        "buyers_simulated": total_simulated,
        "successful_matches": successful_matches,
        "failed_matches": failed_matches,
        "constraint_satisfaction_rate": satisfaction_rate,
        "average_score": avg_score,
        "friction_distribution": friction_summary,
        "persona_success_rates": {
            p: round(persona_success_count.get(p, 0) / max(sum(1 for e in evaluations if e["full_persona_name"] == p), 1), 2)
            for p in set(e["full_persona_name"] for e in evaluations)
        },
        "metric_type": "SIMULATED RESULT",
    }

    # 5. ONLY AFTER all decision, summary, and recommendation calculations are complete:
    # Truncate serialized & persisted rankings representation
    results: List[SimulationResultItem] = []
    db_results = []

    for ev in evaluations:
        sim_out = ev["sim_output"]
        sel_id = ev["selected_id"]
        persona_name = ev["full_persona_name"]
        weights = ev["weights"]
        intent_dict = ev["intent_dict"]

        full_rankings = sim_out["rankings"]
        total_evaluated = len(full_rankings)
        total_eligible_count = sum(1 for r in full_rankings if r.get("passed") is True)
        total_disqualified_count = sum(1 for r in full_rankings if r.get("passed") is False)

        truncated_rankings = truncate_rankings(
            rankings=full_rankings,
            selected_product_id=sel_id,
            max_passed=20,
            max_disqualified=10,
        )

        results.append(SimulationResultItem(
            persona_name=persona_name,
            selected_product_id=sel_id,
            score=sim_out["score"],
            constraints_satisfied=sim_out["constraints_satisfied"],
            reason_codes=sim_out["reason_codes"],
            frictions=sim_out["frictions"],
            rankings=truncated_rankings,
            explanation=sim_out["explanation"],
            intent=intent_dict,
            persona_weights=weights,
            total_products_evaluated=total_evaluated,
            total_eligible=total_eligible_count,
            total_disqualified=total_disqualified_count,
            score_breakdown=sim_out.get("score_breakdown"),
            selected_product_name=sim_out.get("selected_product_name"),
            selected_product_price=sim_out.get("selected_product_price"),
            selected_product_category=sim_out.get("selected_product_category"),
        ))

        db_results.append(SimulationResult(
            id=uuid.uuid4(),
            persona_name=persona_name,
            selected_product_id=sel_id,
            score=sim_out["score"],
            constraints_satisfied=sim_out["constraints_satisfied"],
            reason_codes=sim_out["reason_codes"],
            frictions=sim_out["frictions"],
            rankings=truncated_rankings,
            explanation=sim_out["explanation"],
        ))

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
        recommendation_service.generate_recommendations(
            db,
            merchant_id,
            detailed_frictions,
            simulation_run_id=sim_id,
            scenario_count=total_simulated,
        )

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

