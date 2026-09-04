# Document 5: SIMULATION_ENGINE_INTERNALS
> Core merchant-side differentiator. All data from actual code.

---

## A. Buyer Persona Weight Vectors

**Source:** `backend/app/api/v1/optimization/simulations.py:22-28`

```python
PERSONA_PROFILE_MAP = {
    "BUDGET":   {"price": 0.50, "offers": 0.25, "delivery": 0.10, "quality": 0.10, "returns": 0.05},
    "SPEED":    {"delivery": 0.55, "metadata": 0.20, "quality": 0.15, "price": 0.10},
    "QUALITY":  {"quality": 0.50, "metadata": 0.20, "returns": 0.15, "delivery": 0.10, "price": 0.05},
    "FEATURE":  {"metadata": 0.50, "quality": 0.25, "price": 0.15, "delivery": 0.10},
    "BALANCED": {"price": 0.25, "quality": 0.25, "delivery": 0.20, "returns": 0.15, "offers": 0.10, "metadata": 0.05},
}
```

**Configurable?** `PERSONA_PROFILE_MAP` is hardcoded. DB personas are a fallback only if profile name is not in the map. Merchants can create custom personas via `POST /buyer-personas` but these are only used if no PERSONA_PROFILE_MAP match exists.

---

## B. Scenario Variant Pool

**Source:** `simulations.py:31-67`  
Format: `(label, max_budget_paise, requirements_list, delivery_deadline_days_or_None)`

5 curated base variants per persona + Cartesian product extension for runs > 5 scenarios.
All budget values in **paise**. e.g. 500000 = ₹5,000, 3000000 = ₹30,000.

SCENARIO_WEIGHT_OVERRIDES only exist for QUALITY sub-variants (quality_essentials through quality_balanced).  
BUDGET, SPEED, FEATURE, BALANCED variants use base PERSONA_PROFILE_MAP weights.

---

## C. Scoring Formula (exact code)

**Source:** `backend/app/simulation/scoring.py:15-130`

```python
# Weighted sum (unnormalized)
raw_score = (
    (price_score   * w_price)    +
    (delivery_score * w_delivery) +
    (quality_score  * w_quality)  +
    (return_score   * w_returns)  +
    (offer_score    * w_offers)   +
    (metadata_score * w_metadata)
) / total_w

final_score = min(max(raw_score, 0.0), 1.0)  # clamp, no rounding
```

**Component formulas:**

```python
# Price (scoring.py:41-56)
if price <= max_budget:
    savings_ratio = (max_budget - price) / max_budget
    if w_price >= 0.3:  price_score = 0.5 + (0.5 * savings_ratio)
    else:               price_score = 0.8 + (0.2 * savings_ratio)
else:
    price_score = max(0.0, 0.5 - ((price - max_budget) / max_budget))
# If no budget: price_score = max(0.1, 1.0 - (price / 2_000_000.0))

# Delivery (scoring.py:59-71)
delivery_days   <= 1: score=1.0 | <= 2: 0.90 | <= 3: 0.75 | <= 5: 0.55 | <= 7: 0.40
delivery_days   > 7: max(0.1, 1.0 - (days/14.0))
delivery = None: 0.30

# Quality (scoring.py:75-95)
rating_score = min(max(float(rating)/5.0, 0.0), 1.0) * 0.7    # if rating exists
rating = None: 0.35
has_warranty = 0.2 (True) | 0.05 (None) | 0.0 (False)
is_premium   = 0.1 (True) | 0.0 (False/None)
quality_score = min(1.0, rating_score + has_warranty + is_premium)

# Returns (scoring.py:97-109)
return_days >= 30: 1.0 | >= 14: 0.85 | >= 7: 0.60 | < 7: 0.10
return = None + return_policy exists: 0.50  |  None completely: 0.20

# Offers (scoring.py:112-117)
discount_percent > 0: min(1.0, 0.4 + (pct/50.0)*0.6)
has_offer/has_discount (bool): 0.75
else: 0.10

# Metadata (scoring.py:120-127)
desc_score = min(0.4, (len(description)/500.0) * 0.4)   # max 0.4 at 500 chars
meta_score = min(0.6, (len(metadata_keys)/15.0) * 0.6)   # max 0.6 at 15 keys
metadata_score = desc_score + meta_score
```

**Deterministic?** YES. float64, no rounding, no randomness.

---

## D. Ranking / Tie-Breaking

**Source:** `backend/app/simulation/engine.py:65`

```python
candidates.sort(
    key=lambda x: (-x["score"], str(x["product_id"]))
)
selected = candidates[0]  # always top-1
```

UUID string sort for tie-breaking is deterministic and order-invariant (same result regardless of input order).

---

## E. Metadata Field Usage

| Field | Used in Simulation? | Where | Notes |
|---|---|---|---|
| `name` | YES | `engine.py:29` | Used in explanation text; included in requirements free-text match |
| `description` | YES | `friction.py:44`, `scoring.py:120` | Hard constraint free-text + metadata_score desc component |
| `price` | YES | `friction.py:36`, `scoring.py:41` | Hard constraint + price_score |
| `is_active` | YES | `friction.py:40` | Hard constraint: inactive → INVENTORY_ISSUE |
| `available_quantity` | YES | `friction.py:41` | Hard constraint: <= 0 → INVENTORY_ISSUE; None = unmanaged (no friction) |
| `metadata.delivery_days` | YES | `friction.py:56`, `scoring.py:59` | Hard constraint + delivery_score |
| `metadata.return_days` | YES | `friction.py (soft)`, `scoring.py:97` | Soft friction + return_score |
| `metadata.rating` / `product_rating` / `overall_rating` | YES | `normalization.py:36`, `scoring.py:75` | Normalized by MetadataNormalizer, used in quality_score |
| `metadata.warranty` | YES | `normalization.py:74`, `scoring.py:84` | Normalized, used in quality_score |
| `metadata.discount_percent` | YES | `scoring.py:112` | Offer score component |
| `metadata.has_offer` / `has_discount` | YES | `scoring.py:115` | Offer score fallback |
| `metadata.high_quality` / `premium` | YES | `scoring.py:90` | Premium flag in quality_score |
| `metadata.return_policy` | YES | `scoring.py:104` | Soft returns fallback if return_days absent |
| `metadata.specifications` | PARTIAL | `normalization.py:82` | Warranty extracted from specs dict; spec count used in metadata_score |
| `category` | NO | — | Not used in simulation engine; only in catalogue search |
| `currency` | NO | — | Retrieved but not used in simulation |

---

## F. Intent Parameters vs. Simulation Usage

| Intent Field | Extracted by LLM? | Used in Simulation Hard Constraint? | Used in Scoring? |
|---|---|---|---|
| `max_budget` | YES | YES (PRICE_MISMATCH) | YES (price_score) |
| `requirements` | YES | YES (MISSING_FEATURE) | NO |
| `delivery_deadline_days` | YES | YES (DELIVERY_TOO_SLOW, DELIVERY_UNKNOWN) | NO |
| `category` | YES | NO | NO (catalogue search only) |
| `min_budget` | YES | **NO** | **NO** |
| `preferences` | YES | **NO** | **NO** |

---

## G. Friction Types (Complete List)

**Source:** `backend/app/simulation/friction.py`

| Friction | Hard/Soft | Trigger Condition | Leads to Product Rejection? |
|---|---|---|---|
| `PRICE_MISMATCH` | HARD | `price > intent.max_budget` | YES |
| `INVENTORY_ISSUE` | HARD | `is_active == False` OR `available_quantity <= 0` | YES |
| `MISSING_FEATURE` | HARD | Required feature not in metadata or product text | YES |
| `DELIVERY_UNKNOWN` | HARD | Intent has deadline AND product has no `delivery_days` | YES |
| `DELIVERY_TOO_SLOW` | HARD | `product.delivery_days > intent.delivery_deadline_days` | YES |
| `DELIVERY_UNCLEAR` | SOFT | `w_delivery >= 0.20` AND no `delivery_days` in metadata | NO (score penalty only) |
| `RETURN_UNCLEAR` | SOFT | `w_returns >= 0.10` AND no `return_days` or `return_policy` | NO |
| `INSUFFICIENT_PRODUCT_INFORMATION` | SOFT | `description < 15 chars` OR (`w_metadata >= 0.20` AND `metadata < 2 keys`) | NO |
| `NO_SUITABLE_PRODUCT` | Engine | All products rejected by hard constraints | Synthetic (no candidates) |

---

## H. Recommendation Rules

| Friction | Rec Type | Suggested Fix | Hardcoded Values | File | Line |
|---|---|---|---|---|---|
| `PRICE_MISMATCH` | `PRICE_COMPETITIVENESS` | 10% price reduction | `price_reduction_percent=10` | `recommendation_service.py` | ~120 |
| `DELIVERY_TOO_SLOW` / `DELIVERY_UNKNOWN` | `DELIVERY_SPEED_SLA` | Set `delivery_days=2` | `new_delivery_days=2` | `recommendation_service.py` | ~140 |
| `RETURN_UNCLEAR` | `RETURN_POLICY_CLARITY` | Set `return_days=14` | `new_return_days=14` | `recommendation_service.py` | ~165 |
| `MISSING_FEATURE` | `MISSING_FEATURE` | Add structured specs | None (advisory only) | `recommendation_service.py` | ~180 |
| `INSUFFICIENT_PRODUCT_INFORMATION` | `CATALOGUE_ENRICHMENT` | Enrich description/metadata | None (advisory only) | `recommendation_service.py` | ~195 |
| `INVENTORY_ISSUE` | `INVENTORY_RESTORATION` | Restock to 50 units | `new_inventory_count=50` | `recommendation_service.py` | ~205 |

---

## I. What-If Delta Formula

**Source:** `backend/app/services/optimization/what_if_service.py`

```python
# Division-by-zero guard at line ~105
if b_avg_score > 0:
    delta_pct = round(((p_avg_score - b_avg_score) / b_avg_score) * 100.0, 1)
elif p_avg_score > 0:
    delta_pct = 100.0
else:
    delta_pct = 0.0
```

- **In-memory clone?** YES: `modified_catalogue = copy.deepcopy(baseline_catalogue)` (line 59)
- **DB mutation?** NO: only `WhatIfRun` metrics persisted (not product changes)
- **Metric type:** `simulated_selection_rate` (not "probability of sale")

---

## J. Scale & Performance

| Metric | Value | Source |
|---|---|---|
| Products per scenario | ALL active (e.g. 2,977) | `product_repository.py:58` |
| Max scenarios per run | `req.scenario_count` (default 20, no hard cap in code) | `simulations.py` |
| DB retrieval time (2,977 products) | ~137ms median (empirically measured) | Step 3 benchmark |
| 20-scenario run latency | ~1.95s | Step 3 benchmark |
| 40-scenario run latency | ~3.7s | Step 3 benchmark |
| What-If latency | ~1.28s | Step 3 benchmark |
| Ranking payload (40 scenarios) | 154 KB (after truncation) vs 25 MB (full) | Step 3 benchmark |
| Response truncation: max passed | 20 | `simulations.py:171` |
| Response truncation: max disqualified | 10 | `simulations.py:172` |
| Winner always included | YES | `truncate_rankings()` winner preservation logic |
