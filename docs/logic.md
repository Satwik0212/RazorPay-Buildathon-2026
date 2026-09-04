# Razorpay AI Commerce Platform — Canonical Logic Reference

This document is the ultimate source of truth for the logic, formulas, and deterministic rules governing the Razorpay AI Commerce Platform as currently implemented in the repository.

---

## A. Catalogue

### Metric: Total Products
**Meaning:** The count of all product records for a given merchant in the database, regardless of active status.
**Source:** `backend/app/api/v1/analytics.py -> get_merchant_intelligence()`
**Inputs:** 
- `merchant_id`
**Formula:**
```text
SELECT COUNT(id) FROM products WHERE merchant_id = :merchant_id
```

### Metric: Active Products
**Meaning:** The count of products where `is_active = True`.
**Source:** `backend/app/api/v1/analytics.py -> get_merchant_intelligence()`
**Inputs:** 
- `merchant_id`
**Formula:**
```text
SELECT SUM(CAST(is_active AS Integer)) FROM products WHERE merchant_id = :merchant_id
```

### Metric: Total Categories
**Meaning:** The count of unique non-null categories assigned to products.
**Source:** `backend/app/api/v1/analytics.py -> get_merchant_intelligence()`
**Formula:**
```text
SELECT COUNT(DISTINCT(category)) FROM products WHERE merchant_id = :merchant_id
```

### Metric: Total Inventory (Available Stock)
**Meaning:** The sum of `available_quantity` across all inventoried products for a merchant.
**Source:** `backend/app/api/v1/analytics.py -> get_merchant_intelligence()`
**Formula:**
```text
SELECT SUM(inventory.available_quantity) 
FROM inventory 
JOIN products ON inventory.product_id = products.id 
WHERE products.merchant_id = :merchant_id
```

### Metric: Product Price
**Meaning:** The canonical price of a product in the database.
**Source:** `backend/app/models/product.py -> Product.price`
**Inputs:** None (stored field)
**Formula:**
```text
product.price (Stored as a BigInteger representing minor units, e.g., paise for INR)
```
**Notes:** All backend simulation and what-if logic treats `price` in minor units. Custom simulation input budget is converted by `max_budget * 100` if not already in paise.

### Metric: Catalogue Retrieval for Simulation / What-If
**Meaning:** The set of products analyzed by the simulation and What-If engines.
**Source:** `backend/app/repositories/product_repository.py -> get_active_catalogue_for_merchant()`
**Inputs:**
- `merchant_id`
**Formula:**
```text
SELECT products.*, inventory.available_quantity
FROM products
LEFT JOIN inventory ON products.id = inventory.product_id
WHERE products.merchant_id = :merchant_id AND products.is_active = TRUE
ORDER BY products.id
```
**Notes:** Evaluates ALL active products (e.g., 2,977 for a merchant) in a single query. Unmanaged inventory returns `available_quantity = None`. There is no `COALESCE(..., 10)` fallback.

---

## B. AI Buyer / Intent

The simulation relies on predefined deterministic personas (e.g., `BUDGET`, `SPEED`, `QUALITY`, `BALANCED`) and dynamically generates scenarios with varying strictness (e.g., changing `max_budget`, `requirements`, and `delivery_deadline_days`).

### Metric: Persona Scenario Generation
**Meaning:** How scenarios are generated for the 20-scenario default run.
**Source:** `backend/app/api/v1/optimization/simulations.py -> run_simulation()`
**Notes:**
Scenarios iterate through selected base personas. It uses `SCENARIO_VARIANTS` and expands into extended deterministic combinations (`_build_expanded_variant_pool`).
The intent is a dictionary (e.g., `{"max_budget": max_budget, "requirements": [...], "delivery_deadline_days": 3}`).

---

## C. Simulation

### Metric: Scenario Count (Total Simulated)
**Meaning:** The number of simulated buyer evaluations executed.
**Source:** `backend/app/api/v1/optimization/simulations.py -> run_simulation()`
**Inputs:**
- `req.scenario_count` (Default is 20)
**Formula:**
```text
total_simulated = len(evaluations)
```

### Metric: Constraint Satisfaction Rate (Match Rate)
**Meaning:** The proportion of simulated scenarios that successfully found at least one eligible product that passed all hard constraints.
**Source:** `backend/app/api/v1/optimization/simulations.py -> run_simulation()`
**Inputs:**
- `evaluations` list
**Formula:**
```text
successful_matches = sum(1 for e in evaluations if e["sim_output"]["constraints_satisfied"] and e["selected_id"] is not None)
satisfaction_rate = round(successful_matches / MAX(total_simulated, 1), 3)
```

### Metric: Average Score
**Meaning:** The average score of the selected winning products across all simulated scenarios (including 0 for scenarios with no winner).
**Source:** `backend/app/api/v1/optimization/simulations.py -> run_simulation()`
**Formula:**
```text
avg_score = round(sum(e["sim_output"]["score"] for e in evaluations) / MAX(total_simulated, 1), 3)
```

### Metric: Rankings Truncation
**Meaning:** To prevent payload bloat, the simulation evaluates 100% of the active catalogue but truncates the serialized output.
**Source:** `backend/app/api/v1/optimization/simulations.py -> truncate_rankings()`
**Notes:** The backend returns exactly a maximum of 31 items per scenario (top 20 passed + top 10 disqualified + winner if not already present). Friction metrics and recommendations are generated *before* this truncation using the full 100% evaluation results.

---

## D. Hard Constraints

### Metric: Constraint Pass/Fail
**Meaning:** Hard rejection filter that disqualifies a candidate product for a given buyer scenario.
**Source:** `backend/app/simulation/friction.py -> FrictionDetector.detect_hard_constraints()`
**Inputs:**
- `product`, `intent`
**Formulas:**
1. **Price Mismatch:**
   ```text
   if price > intent.max_budget: append(FrictionReason.PRICE_MISMATCH)
   ```
2. **Inventory Issue:**
   ```text
   if not product.is_active: append(FrictionReason.INVENTORY_ISSUE)
   if product.available_quantity is not None AND product.available_quantity <= 0: append(FrictionReason.INVENTORY_ISSUE)
   ```
   *(Note: unmanaged inventory `None` is NOT penalized).*
3. **Missing Feature:**
   Checks structured metadata (`metadata.get(requirement) == "true"`). If not found, checks for the presence of the requirement text in the product `name + description`, while rejecting if negative phrases (e.g., "no <req>", "without <req>") are found.
4. **Delivery Deadline:**
   ```text
   if intent.delivery_deadline_days is not None:
       if product.delivery_days is None: append(FrictionReason.DELIVERY_UNKNOWN)
       elif product.delivery_days > intent.delivery_deadline_days: append(FrictionReason.DELIVERY_TOO_SLOW)
   ```

---

## E. Scoring

### Metric: Product Score
**Meaning:** Deterministic weighted sum (range [0.0, 1.0]) scoring a product's appeal to a specific buyer persona.
**Source:** `backend/app/simulation/scoring.py -> ProductScorer.calculate_score()`
**Inputs:**
- `product`, `persona_weights`, `max_budget_minor`
**Formula:**

```text
raw_score = (
    (price_score * w_price) +
    (delivery_score * w_delivery) +
    (quality_score * w_quality) +
    (return_score * w_returns) +
    (offer_score * w_offers) +
    (metadata_score * w_metadata)
) / total_weights

final_score = MIN(MAX(raw_score, 0.0), 1.0)
```
*(Precision is float64, unrounded at the scorer level to prevent artificial ties).*

**Component Formulas:**
- **Price Score:** 
  If price <= budget and `w_price >= 0.3`: `0.5 + (0.5 * MIN(MAX(savings_ratio, 0.0), 1.0))`
  If price <= budget and `w_price < 0.3`: `0.8 + (0.2 * MIN(MAX(savings_ratio, 0.0), 1.0))`
  If price > budget: `MAX(0.0, 0.5 - ((price - budget) / budget))`
- **Delivery Score:** <=1 day (1.0), <=2 (0.9), <=3 (0.75), <=5 (0.55), <=7 (0.40), >7 (`MAX(0.1, 1.0 - (days/14.0))`), Unknown (0.30)
- **Quality Score:** `MIN(1.0, (rating/5.0 * 0.7) + has_warranty + is_premium)`
- **Return Score:** >=30 days (1.0), >=14 (0.85), >=7 (0.60), <7 (0.10). Unknown with policy (0.50), Unknown without policy (0.20)
- **Offer Score:** Based on `discount_percent` `MIN(1.0, 0.4 + (pct/50) * 0.6)` or `has_offer` boolean (0.75).
- **Metadata Score:** Combination of description length (max 0.4 at 500 chars) and metadata key count (max 0.6 at 15 keys).

---

## F. Scenario Weights

### Metric: Weights Resolution
**Meaning:** Base persona weights are overriden by specific scenario combinations if defined.
**Source:** `backend/app/api/v1/optimization/simulations.py -> _resolve_persona_weights()`
**Logic:**
```text
1. Fetch base_weights for persona from DB or default to BALANCED.
2. If variant_label (e.g. "budget_strict") exists in SCENARIO_WEIGHT_OVERRIDES:
       weights = SCENARIO_WEIGHT_OVERRIDES[variant_label]
```
Calculations are request-local and do not mutate global persona profiles.

---

## G. Ranking / Tie Breaking

### Metric: Candidate Sort Order
**Meaning:** Determines the final ranking and the selected winner.
**Source:** `backend/app/simulation/engine.py -> SimulationEngine.run_simulation()`
**Formula:**
```text
candidates.sort(key=lambda x: (-x["score"], str(x["product_id"])))
```
**Notes:** Tie-breaking is completely deterministic. If two products have the exact same float64 score, they are sorted alphabetically by their UUID string. The `#1` ranked candidate is selected as the winner.

---

## H. Friction Detection

### Metric: Friction Signals
**Meaning:** A count of the exact reasons a product failed a hard constraint or tripped a soft penalty.
**Source:** `backend/app/api/v1/optimization/simulations.py`
**Notes:**
A single product can generate multiple friction signals (e.g., `PRICE_MISMATCH` and `MISSING_FEATURE` simultaneously).
A single product evaluated across 40 scenarios might generate 40 separate signals for `PRICE_MISMATCH`. 
Therefore, `6,330 friction signals` across 2,977 products means there were 6,330 individual friction evaluation hits across the cartesian product of (Scenarios × Catalogue). It is NOT a count of unique products.

---

## I. Recommendations

### Metric: Recommendation Generation
**Meaning:** Generates actionable mutations to products to resolve frictions.
**Source:** `backend/app/services/optimization/recommendation_service.py -> generate_recommendations()`
**Logic:**
Groups all friction signals by `reason` and aggregates the count. Finds the `top_product_uuid` with the most hits for that reason.
- **`PRICE_MISMATCH`** -> Suggests 10% price reduction (`new_price_mode="percent_discount"`, `new_price_discount_pct=10`).
- **`RETURN_UNCLEAR`** -> Suggests setting return_days to 14 (`new_return_days=14`).
- **`INVENTORY_ISSUE`** -> Suggests restocking to 50 (`new_inventory_count=50`).
Database persistence: Saved to `OptimizationRecommendation` with `status="PROPOSED"`. If a recommendation for a given type already exists as PROPOSED, it updates the existing record with the new friction count and impact, ensuring idempotency per merchant per friction type.

---

## J. What-If Simulator

### Metric: What-If Delta
**Meaning:** Computes the difference in match rate and average score when a product is modified in-memory.
**Source:** `backend/app/services/optimization/what_if_service.py -> run_what_if()`
**Logic:**
1. Create deep copy of the full active catalogue.
2. Apply `price`, `delivery_days`, `return_days`, and `metadata` overrides to the specific `product_id` in-memory.
3. Run simulation engine across all scenarios on the baseline catalogue.
4. Run simulation engine across all scenarios on the modified catalogue.
5. Compute delta:
```text
delta_pct = round(((proposed_avg_score - baseline_avg_score) / baseline_avg_score) * 100.0, 1)
```
**Notes:** 
- The What-If simulation operates at the **catalogue level**, evaluating the entire full active catalogue for both baseline and proposed states.
- It uses deterministic matching and scoring, NOT a literal probability-of-sale prediction model. Terminology used is `simulated_selection_rate` and `average_score`.
- No database records are mutated during the What-If simulation.

---

## K. Payment

### Metric: Order Amount
**Meaning:** Total cost of an order to be charged to the customer.
**Source:** `backend/app/services/quote_service.py -> create_quote()`
**Inputs:**
- Cart items, Database Products
**Formula:**
```text
subtotal = SUM(product.price * item.quantity)
total = MAX(0, subtotal - discount + shipping + tax)
```
**Notes:** 
- Price is sourced authoritatively from `Product.price` in the DB (in paise).
- `quote.total` is passed directly to the `RazorpayOrdersAdapter.create_order(amount=quote.total)` unchanged. Razorpay expects paise, so the unit aligns perfectly.

### Metric: Idempotency
**Meaning:** Ensures duplicate payments or orders are not created.
**Source:** `backend/app/services/checkout_service.py -> create_checkout_order()`
**Logic:**
```text
existing_order = order_repo.get_by_authorization_id(authorization_id)
if existing_order: return existing_order
```
Also guarded by a database-level unique constraint on `authorization_id`.

---

## L. Analytics

### Metric: Persona Performance
**Meaning:** Success rate and average score aggregated per persona across past SimulationRuns.
**Source:** `backend/app/api/v1/analytics.py -> get_merchant_intelligence()`
**Logic:**
Iterates through all `SimulationResult` records for a merchant and groups them by `persona_name`.
```text
avg_score = score_sum / total_simulations
```

---

## M. Audit / Governance

### Metric: Audit Events
**Meaning:** Immutable log of system and user actions.
**Source:** `backend/app/services/audit_service.py`
**Logged Actions:**
- `QUOTE_CREATED` (Total, Cart ID)
- `ORDER_CREATED` (Razorpay ID, Amount)
- Product manipulations, Auth grants.

---

## N. Frontend Transformations

### Metric: Match Rate / Win Rate
**Source:** `frontend/src/pages/merchant/Optimization.tsx`
**Logic:** 
Frontend receives `summary_metrics.constraint_satisfaction_rate` (e.g., `0.725`) and often displays it as `72.5%` or simply `72%` by `(rate * 100).toFixed(0)`.

### Metric: Friction Counts
**Source:** `frontend/src/components/features/simulation/SimulationDashboard.tsx`
**Logic:**
The frontend receives the aggregated `friction_distribution` dictionary (e.g. `{"PRICE_MISMATCH": 1200}`) which represents *signals* across scenarios, not unique products.

---

## O. Custom Simulation

### Metric: Custom Buyer Override
**Meaning:** An endpoint parameter allowing the client to execute a simulation with explicit constraints rather than the default persona matrix.
**Source:** `backend/app/api/v1/optimization/simulations.py`
**Logic:**
```text
If req.custom_buyer is present:
    intent["max_budget"] = req.custom_buyer.max_budget * 100
    intent["requirements"] = req.custom_buyer.requirements
    intent["delivery_deadline_days"] = req.custom_buyer.delivery_deadline_days
    weights = req.custom_buyer.weights
```
**Notes:** Implemented and functional. Directly overrides persona generation, sets scenario names to `CUSTOM:name`, and calculates budget by multiplying input by 100 to convert to paise.

---

## P. Edge Cases

- **Zero eligible products:** All scenarios run but return `constraints_satisfied=False` and `selected_product_id=None`. Average score is mathematically robust due to `MAX(total_simulated, 1)` divisor, resulting in `0.0`.
- **Missing Delivery:** Assigned a `DELIVERY_UNKNOWN` friction if a deadline is present, leading to hard rejection. Otherwise, receives a penalty (score=0.30).
- **Missing Warranty:** Defaults to `0.05` quality score boost (slight bump for uncertainty compared to 0.20 for verified warranty).
- **Empty Catalogue:** For What-If, raises `ValidationError("Merchant catalogue is empty")`.
- **Payment Signature Invalid:** Razorpay webhook verification fails, returns 400 Bad Request, preventing inventory decrement.
