# P1 Tech & Logic — AI Commerce Platform

> **Purpose:** This document defines the implementation-level technology, API contracts, backend logic, data flow, scoring logic, and frontend behavior for the P1 features.
>
> **P1 is built only after the P0 transaction flow is stable.** P1 must improve differentiation and product depth without destabilizing payment execution.

---

# 0. P1 Scope

The P1 layer contains:

1. **Advanced AI Buyer Personas**
2. **Detailed AI Buyer Simulation**
3. **Explainable Optimization Recommendations**
4. **Advanced Merchant Analytics**
5. **Advanced Merchant Policy Controls**
6. **AI Commerce Readiness Improvements**
7. **Optimization What-If Engine**
8. **P1 Audit / Explainability Enhancements**

The central P1 loop is:

```text
Merchant Catalogue
       ↓
Buyer Personas
       ↓
AI Buyer Simulation
       ↓
Selection / Rejection Analysis
       ↓
Readiness + Weakness Detection
       ↓
Optimization Suggestions
       ↓
What-If Simulation
       ↓
Merchant Decision
       ↓
Improved Merchant Configuration
       ↓
Repeat Simulation
```

---

# 1. Technology Stack

## Frontend

- React
- TypeScript
- React Router
- Tailwind CSS
- Recharts or another lightweight charting library
- Fetch / Axios for API calls

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

## AI

Use an LLM provider through a thin internal adapter.

```text
AIService
   ↓
LLMProviderAdapter
   ↓
LLM API
```

The application should not directly scatter LLM API calls across business logic.

## Payments

Razorpay Test Mode:

- Orders API
- Standard Checkout
- Webhooks

Razorpay's current Standard Checkout flow requires creating an Order server-side and passing the returned `order_id` to Checkout. Razorpay also recommends using webhooks for server-side payment confirmation rather than treating a client callback as the authoritative payment state. citeturn0search0turn0search5

## Database

PostgreSQL.

---

# 2. Core P1 Architecture

```text
                        MERCHANT
                           │
                           ▼
                  ┌─────────────────┐
                  │ React Dashboard │
                  └────────┬────────┘
                           │
                           ▼
                    FastAPI API Layer
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
       Persona Engine   Simulation     Analytics
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                    Readiness Engine
                           │
                           ▼
                   Optimization Engine
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
           What-If Simulator    Recommendations
                 │                   │
                 └─────────┬─────────┘
                           ▼
                    Merchant Decision
```

---

# 3. Important Engineering Rule

P1 is an **analysis and optimization layer**.

It must not directly modify financial execution.

```text
P1 AI
  ↓
Recommendation
  ↓
Merchant Decision
  ↓
P0 deterministic backend
  ↓
Policy
  ↓
Authorization
  ↓
Razorpay
```

For example:

```text
AI Recommendation
      ↓
Merchant reviews
      ↓
Merchant clicks "Apply"
      ↓
Backend validates ownership + allowed field
      ↓
Product updated
      ↓
Simulation can be rerun
```

The AI must never directly modify a merchant's price without an explicit merchant action. Do not require a complex approve/reject/apply state machine.

---

# 4. Feature #1 — Advanced AI Buyer Personas

## Purpose

Instead of simulating one generic AI buyer, create multiple buyer types with different priorities.

Example:

```text
Budget Buyer
Speed Buyer
Quality Buyer
Balanced Buyer
```

Additional personas are optional/future.

The same product catalogue can therefore produce different outcomes depending on the buyer.

---

## 4.1 Persona Data Model

```text
BuyerPersona

id
merchant_id / system_owned
name
description
budget_weight
price_weight
delivery_weight
quality_weight
return_policy_weight
offer_weight
metadata_weight
created_at
updated_at
```

Example:

```json
{
  "name": "Budget Buyer",
  "price_weight": 0.40,
  "delivery_weight": 0.10,
  "quality_weight": 0.15,
  "return_policy_weight": 0.10,
  "offer_weight": 0.20,
  "metadata_weight": 0.05
}
```

Weights must sum to 1.

---

# 5. Persona Creation Logic

For MVP/P1, personas should primarily be **configuration**, not unrestricted LLM-generated personalities.

```text
Persona
   ↓
Weights + Constraints
   ↓
Deterministic Scoring
   ↓
Optional LLM Explanation
```

This keeps the simulation reproducible.

The LLM can generate natural-language descriptions, but the actual scoring should remain deterministic.

---

# 6. Persona API

### List personas

```http
GET /api/v1/buyer-personas
```

Response:

```json
[
  {
    "id": "budget",
    "name": "Budget Buyer",
    "weights": {
      "price": 0.40,
      "delivery": 0.10,
      "quality": 0.15,
      "returns": 0.10,
      "offers": 0.20,
      "metadata": 0.05
    }
  }
]
```

### Create custom persona

```http
POST /api/v1/buyer-personas
```

Request:

```json
{
  "name": "Fast Delivery Buyer",
  "weights": {
    "price": 0.10,
    "delivery": 0.45,
    "quality": 0.20,
    "returns": 0.10,
    "offers": 0.05,
    "metadata": 0.10
  }
}
```

Backend validates:

```text
all weights >= 0
sum(weights) == 1
```

---

# 7. Feature #2 — Detailed AI Buyer Simulation

## Purpose

Simulate how AI buyers discover, filter, rank, and select products.

This is the heart of P1.

```text
Buyer Intent
     ↓
Persona
     ↓
Catalogue
     ↓
Hard Constraints
     ↓
Candidate Products
     ↓
Feature Extraction
     ↓
Weighted Scoring
     ↓
Ranking
     ↓
Selected Product
     ↓
Explanation
```

---

# 8. Simulation Input

```json
{
  "merchant_id": "m_123",
  "persona_id": "budget",
  "intent": {
    "category": "headphones",
    "max_budget": 5000,
    "requirements": ["ANC"],
    "delivery_deadline_days": 3
  }
}
```

---

# 9. Simulation Pipeline

## Step 1 — Validate merchant

```text
Authenticated user
      ↓
merchant_id
      ↓
Ownership check
      ↓
Continue
```

---

## Step 2 — Resolve persona

```text
persona_id
    ↓
Load weights
    ↓
Validate weights
```

---

## Step 3 — Parse intent

If intent is entered naturally:

```text
"I need ANC headphones under 5k delivered within 3 days."
```

The LLM extracts:

```json
{
  "category": "headphones",
  "max_budget": 5000,
  "requirements": ["ANC"],
  "delivery_deadline_days": 3
}
```

The output is parsed through Pydantic.

If parsing fails:

```text
LLM output
   ↓
Validation failure
   ↓
Retry / fallback
   ↓
Return structured error
```

---

# 10. Hard Constraint Filtering

Before AI scoring:

```text
Product
 ↓
Active?
 ↓
In stock?
 ↓
Category matches?
 ↓
Price <= budget?
 ↓
Required feature exists?
 ↓
Delivery requirement possible?
```

Anything failing a hard constraint is removed.

This is important because a product with a perfect "AI score" must not win if it violates an explicit requirement.

---

# 11. Product Feature Normalization

Each candidate gets normalized features.

Example:

```json
{
  "price_score": 0.82,
  "delivery_score": 1.0,
  "quality_score": 0.76,
  "return_score": 0.90,
  "offer_score": 0.40,
  "metadata_score": 0.95
}
```

All feature scores should be normalized to:

```text
0.0 → worst
1.0 → best
```

---

# 12. Weighted Persona Score

Example:

```text
score =
    price_score    × price_weight
  + delivery_score × delivery_weight
  + quality_score  × quality_weight
  + return_score   × return_weight
  + offer_score    × offer_weight
  + metadata_score × metadata_weight
```

Example:

```text
Budget Buyer

Price      0.90 × 0.40 = 0.360
Delivery   0.80 × 0.10 = 0.080
Quality    0.75 × 0.15 = 0.113
Returns    0.90 × 0.10 = 0.090
Offers     0.60 × 0.20 = 0.120
Metadata   0.80 × 0.05 = 0.040

Total = 0.803
```

This score is deterministic.

---

# 13. AI Explanation Layer

After ranking, the LLM can explain:

```text
Product A was selected because:
- It is ₹600 below the buyer's budget.
- It meets the ANC requirement.
- Delivery is within the requested window.
- It has a stronger return policy than the alternatives.
```

The explanation must be generated only from structured facts.

The model should not invent:

- prices
- stock
- delivery dates
- policies
- discounts

---

# 14. Simulation API

> **Hackathon Engineering Note:** For the Razorpay Buildathon, the simulation workload (a few personas, a few dozen products) is small enough to run synchronously in-process on the same request. No background worker, Redis, or Celery is required. The request returns the complete result synchronously. If scenario counts grow to hundreds, FastAPI `BackgroundTasks` can be introduced — but this is not needed for the P1 demo.

```http
POST /api/v1/optimization/simulations
```

Request:

```json
{
  "merchant_id": "m_123",
  "persona_id": "budget",
  "intent": {
    "category": "headphones",
    "max_budget": 5000,
    "requirements": ["ANC"],
    "delivery_deadline_days": 3
  }
}
```

Response:

```json
{
  "simulation_id": "sim_123",
  "selected_product": "p_42",
  "rankings": [
    {
      "product_id": "p_42",
      "score": 0.803,
      "rank": 1
    },
    {
      "product_id": "p_19",
      "score": 0.741,
      "rank": 2
    }
  ],
  "explanation": "...",
  "constraints_satisfied": true
}
```

---

# 15. Feature #3 — Multi-Scenario Simulation

A single buyer scenario is weak.

P1 should run many scenarios.

```text
                  Merchant Catalogue
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Budget          Speed          Quality
       Buyer           Buyer           Buyer
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Aggregate Results
```

Example:

```text
100 simulated buyer scenarios

Selected merchant product:
43 times

Rejected:
57 times
```

---

# 16. Scenario Generation

Use a controlled scenario library.

Example:

```text
Budget:
"Find the cheapest acceptable product."

Speed:
"Find something that arrives fastest."

Quality:
"Find the best quality product under my budget."

Deal:
"Find the best current deal."

Balanced:
"Find the best overall option."
```

For more variety, the LLM can generate scenario wording, but the underlying constraints should remain structured.

---

# 17. Multi-Simulation API

```http
POST /api/v1/optimization/simulations/batch
```

Request:

```json
{
  "merchant_id": "m_123",
  "product_ids": ["p1", "p2", "p3"],
  "persona_ids": [
    "budget",
    "speed",
    "quality",
    "balanced"
  ],
  "scenario_count": 100
}
```

Response:

```json
{
  "run_id": "run_001",
  "scenario_count": 100,
  "results": {
    "p1": {
      "selected": 42,
      "rejected": 58,
      "selection_rate": 0.42
    }
  }
}
```

---

# 18. Feature #4 — AI Commerce Readiness Improvements

The P0 readiness score becomes more detailed in P1.

## Dimensions

```text
Catalogue
Pricing
Inventory
Delivery
Returns
Offers
Metadata
Transactionability
AI Discoverability
```

Each dimension produces:

```text
score
issues[]
recommendations[]
```

---

# 19. Readiness Rules

Example:

### Catalogue

```text
name exists
description exists
category exists
images exist
attributes exist
```

### Pricing

```text
price exists
currency exists
price format valid
```

### Inventory

```text
stock status available
quantity available
```

### Delivery

```text
delivery region exists
estimated delivery exists
shipping cost exists
```

### Returns

```text
return eligibility exists
return window exists
conditions exist
```

Each rule produces a deterministic result.

---

# 20. Readiness Scoring

Example:

```text
Catalogue       90
Pricing         100
Inventory       95
Delivery        60
Returns         55
Offers          70
Metadata        80
Transaction     100
```

Weighted overall score:

```text
overall =
    catalogue × 0.15
  + pricing × 0.10
  + inventory × 0.10
  + delivery × 0.15
  + returns × 0.10
  + offers × 0.10
  + metadata × 0.10
  + transaction × 0.20
```

Weights are configurable in code.

---

# 21. Readiness API

```http
GET /api/v1/optimization/readiness
```

Response:

```json
{
  "overall": 78,
  "dimensions": {
    "catalogue": 90,
    "pricing": 100,
    "inventory": 95,
    "delivery": 60,
    "returns": 55,
    "offers": 70,
    "metadata": 80,
    "transactionability": 100
  },
  "issues": [
    {
      "code": "RETURN_POLICY_INCOMPLETE",
      "severity": "high",
      "message": "Return window is missing."
    }
  ]
}
```

---

# 22. Feature #5 — Explainable Optimization Recommendations

## Purpose

Convert simulation failures into actionable merchant suggestions.

```text
Simulation
    ↓
Repeated rejection patterns
    ↓
Root-cause rules
    ↓
Candidate improvements
    ↓
Impact simulation
    ↓
Recommendation
```

---

# 23. Root-Cause Detection

Example:

```text
Product selected in 18/100 simulations.

Analysis:
- price caused rejection in 41 cases
- delivery caused rejection in 23 cases
- incomplete returns caused rejection in 14 cases
```

The system can produce:

```text
Priority #1:
Improve delivery information.

Priority #2:
Improve return policy.

Priority #3:
Consider price adjustment.
```

---

# 24. Recommendation Schema

```json
{
  "recommendation_id": "rec_001",
  "product_id": "p_42",
  "type": "delivery",
  "severity": "high",
  "current_state": "4-6 days",
  "suggested_change": "2-3 days",
  "reason": "Speed-focused buyers reject the product.",
  "baseline_score": 0.41,
  "simulated_score": 0.58,
  "confidence": "simulation-supported"
}
```

Do not claim:

```text
"Revenue will increase by 41%."
```

Prefer:

```text
"Selection rate increased from 41% to 58% in the simulation."
```

---

# 25. Recommendation API

```http
GET /api/v1/optimizations?product_id=p_42
```

Optional:

```http
POST /api/v1/optimizations
```

The backend generates recommendations from the latest simulation run.

---

# 26. Feature #6 — What-If Optimization Engine

This is the main P1 differentiator.

The merchant changes one or more variables.

Example:

```text
Current:
price = 5499

What-if:
price = 5199
```

The system does not immediately alter the real product.

It creates a **simulation state**.

---

# 27. Simulation State

```text
Real Merchant Product
        │
        ▼
Clone to Simulation State
        │
        ▼
Apply Hypothetical Changes
        │
        ▼
Run Same Scenarios
        │
        ▼
Compare
```

Data structure:

```json
{
  "product_id": "p_42",
  "overrides": {
    "price": 5199,
    "delivery_days": 3,
    "return_days": 30
  }
}
```

---

# 28. What-If API

```http
POST /api/v1/optimizations/what-if
```

Request:

```json
{
  "product_id": "p_42",
  "overrides": {
    "price": 5199,
    "delivery_days": 3,
    "return_days": 30
  },
  "scenario_set_id": "scenario_set_01"
}
```

Response:

```json
{
  "baseline": {
    "selection_rate": 0.41,
    "average_score": 0.61
  },
  "simulation": {
    "selection_rate": 0.58,
    "average_score": 0.72
  },
  "change": {
    "selection_rate": 0.17,
    "average_score": 0.11
  }
}
```

---

# 29. Hackathon Note: ONE What-If Flow

Make ONE what-if flow mandatory for the hackathon.

Example:
`baseline` → `hypothetical product attribute change` → `same buyer scenarios` → `re-run` → `compare`

Do not create a complex optimization strategy framework or a multi-strategy comparison matrix for the P1 demo. Keep it simple and focused on demonstrating the impact of a single change.

---

# 31. Feature #7 — Advanced Merchant Analytics

P1 analytics should answer:

### What happened?

```text
AI-assisted orders
AI transaction value
selection rate
rejection rate
```

### Why did it happen?

```text
price rejection
delivery rejection
policy rejection
catalogue rejection
```

### What should we change?

```text
top recommendations
top weak products
top weak attributes
```

---

# 32. Analytics Data Pipeline

```text
AI Simulation
      ↓
Simulation Result
      ↓
Store Event
      ↓
Aggregation
      ↓
Merchant Metrics
      ↓
Dashboard
```

Do not calculate everything from raw events on every dashboard request.

For larger datasets, use pre-aggregated metrics.

For the hackathon MVP/P1, PostgreSQL aggregate queries are sufficient.

---

# 33. Analytics Metrics

The minimum useful metrics for the hackathon are:

```text
- scenarios simulated
- selection rate
- rejection rate
- top friction
- baseline
- optimized
- delta
```

Advanced analytics (like exact AI revenue or AOV impact) remain optional for P2.

---

# 34. Analytics API

```http
GET /api/v1/analytics/merchant/overview
```

Response:

```json
{
  "ai_orders": 23,
  "ai_revenue": 48240,
  "average_order_value": 2097,
  "selection_rate": 0.37,
  "rejection_rate": 0.63
}
```

Detailed:

```http
GET /api/v1/analytics/simulations
GET /api/v1/analytics/optimizations
```

---

# 35. Persona Analytics

Example:

```text
                    Selection Rate

Budget Buyer           51%
Speed Buyer            32%
Quality Buyer          68%
Deal Buyer             44%
Balanced Buyer         56%
```

This tells the merchant:

> "Your product performs well with quality-focused buyers but poorly with speed-focused buyers."

That is more useful than one generic score.

---

# 36. Feature #8 — Advanced Merchant Policy Controls

P1 expands P0 governance.

## P0

```text
max amount
blocked categories
approval threshold
```

## P1

Add:

```text
per-category limits
per-agent limits
time-based limits
daily limits
discount limits
maximum cart quantity
high-risk product review
```

---

# 37. Policy Schema

```json
{
  "max_autonomous_amount": 5000,
  "daily_limit": 50000,
  "category_limits": {
    "electronics": 5000,
    "accessories": 2000
  },
  "blocked_categories": [
    "gift_cards"
  ],
  "discount_limit_percent": 10,
  "max_quantity_per_product": 3,
  "require_approval_above": 5000
}
```

---

# 38. Policy Evaluation Order

Policies should be evaluated in a predictable order.

```text
1. Merchant ownership
        ↓
2. Product active
        ↓
3. Category allowed
        ↓
4. Quantity allowed
        ↓
5. Cart amount
        ↓
6. Daily spend
        ↓
7. Discount limit
        ↓
8. Approval threshold
        ↓
9. Final decision
```

Decision:

```text
ALLOW
REVIEW
BLOCK
```

The first hard BLOCK should terminate evaluation.

---

# 39. Policy API

```http
GET /api/v1/merchant/policy
PUT /api/v1/merchant/policy
POST /api/v1/merchant/policy/check
```

Policy check request:

```json
{
  "cart_id": "cart_123",
  "amount": 4600,
  "category": "electronics",
  "quantity": 1
}
```

Response:

```json
{
  "decision": "ALLOW",
  "reasons": [
    "Amount below autonomous limit",
    "Category allowed",
    "Quantity within limit"
  ]
}
```

---

# 40. Feature #9 — P1 Explainability

Every important AI decision should have an explanation object.

```json
{
  "decision": "selected",
  "reason_codes": [
    "UNDER_BUDGET",
    "FAST_DELIVERY",
    "RETURN_POLICY_MATCH"
  ],
  "facts": {
    "price": 4699,
    "budget": 5000,
    "delivery_days": 2,
    "deadline_days": 3
  }
}
```

This is preferable to storing only:

```text
"AI chose Product A because it was better."
```

---

# 41. Explanation Architecture

```text
Deterministic Facts
       ↓
Reason Codes
       ↓
Structured Explanation Object
       ↓
LLM Natural Language
       ↓
Human-readable explanation
```

The LLM verbalizes facts; it does not invent them.

---

# 42. Reason Code System

Example codes:

```text
UNDER_BUDGET
OVER_BUDGET
FAST_DELIVERY
SLOW_DELIVERY
IN_STOCK
OUT_OF_STOCK
RETURN_POLICY_MATCH
RETURN_POLICY_MISSING
OFFER_ADVANTAGE
PRICE_ADVANTAGE
METADATA_COMPLETE
METADATA_INCOMPLETE
CATEGORY_MISMATCH
```

These codes should be stored with simulation results.

---

# 43. P1 Database Additions

Add:

### buyer_personas

```text
id
name
description
weights_json
constraints_json
created_at
updated_at
```

### simulation_runs

```text
id
merchant_id
scenario_count
status
started_at
completed_at
```

### simulation_results

```text
id
run_id
persona_id
product_id
score
rank
selected
reason_codes
feature_scores
```

### optimization_recommendations

```text
id
merchant_id
product_id
type
severity
current_value
suggested_value
baseline_score
projected_score
reason_codes
created_at
```

### what_if_runs

```text
id
merchant_id
product_id
scenario_set_id
overrides_json
baseline_result
simulation_result
created_at
```

### analytics_snapshots

Optional for later scale:

```text
id
merchant_id
date
ai_orders
ai_revenue
selection_rate
average_order_value
```

---

# 44. P1 API Dependency Graph

```text
/api/v1/auth
   ↓
/api/v1/merchants
   ↓
/api/v1/products
   ↓
/api/v1/buyer-personas
   ↓
/api/v1/optimization/simulations
   ↓
/api/v1/optimization/readiness
   ↓
/api/v1/optimizations
   ↓
/api/v1/optimizations/what-if
   ↓
/api/v1/analytics/merchant/overview
```

Every endpoint requires authentication except public auth endpoints.

---

# 45. P1 API Error Model

All APIs should use a common error structure:

```json
{
  "error": {
    "code": "INVALID_SIMULATION",
    "message": "Scenario contains an invalid budget.",
    "request_id": "req_123"
  }
}
```

Example codes:

```text
UNAUTHORIZED
FORBIDDEN
RESOURCE_NOT_FOUND
INVALID_PERSONA
INVALID_SCENARIO
INVALID_OVERRIDE
SIMULATION_FAILED
LLM_UNAVAILABLE
POLICY_BLOCKED
QUOTE_EXPIRED
```

---

# 46. Background Processing

> **Hackathon Rule:** For the Razorpay Buildathon, simulation runs **synchronously in-process**. A single simulation request (a few personas × a few dozen products) completes in seconds. No background worker, no task queue, no Redis is needed. The request returns the complete result directly.

If scenario counts become large enough to cause HTTP timeouts in future iterations, use FastAPI `BackgroundTasks` to run the simulation after returning an accepted response with a `run_id`. The client then polls for completion.

```text
POST /api/v1/optimization/simulations (small scenario count)
        ↓
Run synchronously in-process
        ↓
Return complete result

--- OR --- (only if scenario count causes timeouts)

POST /api/v1/optimization/simulations/batch (large scenario count)
        ↓
Create SimulationRun record
        ↓
Return run_id immediately
        ↓
FastAPI BackgroundTask runs scenarios
        ↓
Store results
        ↓
status = COMPLETED
```

Do **not** introduce Redis, Celery, or RQ for the hackathon. The simulation workload does not require it.

---

# 47. LLM Call Strategy

Avoid one LLM call per product.

Bad:

```text
100 products
 ↓
100 LLM calls
```

Better:

```text
100 products
 ↓
Deterministic filtering
 ↓
10 candidates
 ↓
Structured feature scoring
 ↓
1-2 LLM calls for explanation
```

This reduces:

- latency
- cost
- rate-limit risk
- inconsistent reasoning

---

# 48. LLM Structured Outputs

Every P1 LLM call should target a schema.

Example:

```python
class Intent(BaseModel):
    category: str | None
    max_budget: int | None
    requirements: list[str]
    delivery_deadline_days: int | None
```

And:

```python
class OptimizationSuggestion(BaseModel):
    type: str
    current_value: str
    suggested_value: str
    reason_codes: list[str]
```

Never allow arbitrary free-form model output directly into business logic.

---

# 49. Prompt Architecture

Prompts should be versioned.

```text
prompts/
├── intent_v1.txt
├── explanation_v1.txt
├── optimizer_v1.txt
└── scenario_v1.txt
```

Store the prompt version in simulation metadata.

Example:

```json
{
  "model": "model-name",
  "prompt_version": "optimizer_v1",
  "created_at": "..."
}
```

This makes results reproducible enough for debugging.

---

# 50. Deterministic vs AI Responsibility

Explicit AI Boundary:

**LLM:**
- intent understanding
- semantic interpretation
- explanation
- recommendation explanation

**Deterministic:**
- product filtering
- scoring
- price
- inventory
- quote
- policy
- authorization
- payment state

**The LLM must never become the source of financial truth.**

---

# 51. P1 Frontend Flow — Simulation

```text
Merchant Dashboard
      ↓
AI Buyer Simulator
      ↓
Choose Persona
      ↓
Choose Product / Category
      ↓
Set Scenario
      ↓
Run Simulation
      ↓
Loading / Progress
      ↓
Results
      ↓
Ranking + Reasons
      ↓
Weaknesses
      ↓
Optimize
```

---

# 52. P1 Frontend Flow — Optimizer

```text
Product
  ↓
Current Performance
  ↓
"Improve this"
  ↓
Recommendations
  ↓
Select recommendation
  ↓
What-if preview
  ↓
Before / After
  ↓
Apply or Discard
```

---

# 53. P1 Frontend Flow — Policies

```text
Merchant
  ↓
Policies
  ↓
Spending
Categories
Discounts
Approval
  ↓
Edit
  ↓
Validate
  ↓
Save
  ↓
Audit Event
```

---

# 54. P1 Testing Strategy

## Persona tests

```text
[ ] weights sum to 1
[ ] invalid negative weights rejected
[ ] unknown persona rejected
```

## Simulation tests

```text
[ ] over-budget product excluded
[ ] out-of-stock product excluded
[ ] category mismatch excluded
[ ] deterministic ranking works
[ ] same inputs produce same scores
```

## Readiness tests

```text
[ ] missing return policy lowers score
[ ] missing delivery lowers score
[ ] complete product gets higher score
```

## Optimization tests

```text
[ ] what-if does not mutate real product
[ ] baseline remains unchanged
[ ] identical scenarios are used
[ ] comparison is deterministic
```

## Policy tests

```text
[ ] amount limit
[ ] category limit
[ ] daily limit
[ ] discount limit
[ ] approval threshold
```

---

# 55. P1 Performance Strategy

Avoid unnecessary AI calls.

### Cache

Cache:

- merchant readiness
- catalogue normalization
- persona configurations
- simulation scenario sets

Invalidate when relevant merchant data changes.

Example:

```text
Product updated
     ↓
Invalidate readiness
     ↓
Invalidate affected simulation cache
```

---

# 56. P1 Observability

Every simulation should have:

```text
simulation_id
merchant_id
persona_id
scenario_id
model
prompt_version
start_time
end_time
candidate_count
selected_product
```

Every optimization run:

```text
run_id
baseline_score
new_score
overrides
scenario_count
duration
```

This makes debugging possible when the dashboard shows unexpected results.

---

# 57. P1 Security

### Merchant isolation

Every query must include merchant ownership.

Bad:

```sql
SELECT * FROM products WHERE id = :id;
```

Safer:

```sql
SELECT *
FROM products
WHERE id = :id
AND merchant_id = :authenticated_merchant_id;
```

### Simulation overrides

Never allow:

```text
override = arbitrary JSON → SQL update
```

Instead:

```text
Allowed fields
 ↓
Pydantic schema
 ↓
Validated simulation state
```

### AI-generated recommendations

Never execute directly.

```text
AI recommendation
      ↓
schema validation
      ↓
simulation
      ↓
merchant approval
      ↓
actual change
```

---

# 58. P1 Razorpay Relationship

P1 should not duplicate Razorpay's payment infrastructure.

Instead:

```text
P1 Optimization
       ↓
Improves merchant commerce state
       ↓
P0 Commerce Flow
       ↓
Quote
       ↓
Policy
       ↓
Authorization
       ↓
Razorpay
```

Razorpay Orders are created server-side, and the `order_id` is passed into Checkout. Razorpay's documentation explicitly states that an order should be created for every payment and that payments without an `order_id` cannot be captured and are automatically refunded. citeturn0search0turn0search12

For server-side payment state, use Razorpay webhooks. Webhooks are asynchronous server-to-server notifications, and Razorpay recommends signature verification and idempotent processing. citeturn0search5turn0search3turn0search13

---

# 59. P1 End-to-End Technical Flow

```text
Merchant Login
      ↓
JWT / Session
      ↓
Merchant Dashboard
      ↓
Select Product
      ↓
Readiness Engine
      ↓
Generate Buyer Scenarios
      ↓
Persona Engine
      ↓
Simulation Engine
      ↓
Deterministic Filtering
      ↓
Weighted Scoring
      ↓
AI Explanation
      ↓
Store Simulation Results
      ↓
Analytics Aggregation
      ↓
Weakness Detection
      ↓
Optimization Recommendation
      ↓
Merchant selects What-If
      ↓
Create Simulation State
      ↓
Apply Temporary Overrides
      ↓
Re-run Same Scenarios
      ↓
Compare Baseline / New
      ↓
Merchant chooses:
    ┌───────────────┐
    │               │
  Discard         Apply
    │               │
    │               ▼
    │        Update Merchant Data
    │               │
    │               ▼
    │        Invalidate Cache
    │               │
    └───────┬───────┘
            ▼
       Run Again
```

---

# 60. P1 Implementation Order

Do NOT implement P1 randomly.

## P1.1 — Personas

```text
Persona schema
→ API
→ UI
→ deterministic weights
```

## P1.2 — Simulation

```text
Intent
→ filters
→ scoring
→ ranking
→ result storage
```

## P1.3 — Multi-scenario runs

```text
scenario library
→ batch simulation
→ aggregation
```

## P1.4 — Readiness

```text
rules
→ dimension scores
→ explanations
```

## P1.5 — Recommendations

```text
simulation failures
→ root causes
→ recommendations
```

## P1.6 — What-if

```text
overrides
→ cloned state
→ re-simulation
→ comparison
```

## P1.7 — Analytics

```text
events
→ aggregates
→ dashboard
```

## P1.8 — Advanced policies

```text
category limits
→ daily limits
→ discount limits
→ approval rules
```

## P1.9 — Polish

```text
charts
→ explanations
→ loading states
→ error states
→ audit details
```

---

# 61. What We Should NOT Build in P1

Do not let P1 expand into another project.

Avoid unless everything above is finished:

```text
✕ Complex multi-agent orchestration
✕ Autonomous price changes
✕ Real-world competitor scraping
✕ Large-scale ML training
✕ Reinforcement learning
✕ Real-time market intelligence
✕ Full CRM
✕ Full marketing automation
✕ Complex campaign engine
✕ Production-scale distributed infrastructure
✕ Multiple payment providers
```

The goal is a convincing, deterministic, explainable AI-commerce simulation and optimization system.

---

# 62. P1 Success Criteria

P1 is considered complete when a merchant can:

```text
1. Login
      ↓
2. View AI-readiness
      ↓
3. Choose a buyer persona
      ↓
4. Run a simulation
      ↓
5. See product ranking
      ↓
6. Understand why products won/lost
      ↓
7. See weaknesses
      ↓
8. Receive recommendations
      ↓
9. Run a What-If simulation
      ↓
10. Compare before / after
      ↓
11. Apply a chosen improvement
      ↓
12. Re-run simulation
      ↓
13. See updated analytics
```

The system should produce a clear statement such as:

> **"Under the same 100 buyer scenarios, this change increased simulated selection rate from 41% to 58%."**

That is a much more defensible result than claiming that an AI prediction guarantees additional revenue.

---

# 63. Final P1 Architecture

```text
                         MERCHANT
                            │
                            ▼
                   ┌─────────────────┐
                   │ React Dashboard │
                   └────────┬────────┘
                            │
                            ▼
                     FastAPI APIs
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Personas          Readiness         Analytics
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    Simulation Engine
                            │
                  ┌─────────┴─────────┐
                  ▼                   ▼
          Deterministic Scoring    LLM
                  │              Explanation
                  └─────────┬─────────┘
                            ▼
                    Simulation Results
                            │
                            ▼
                  Root Cause Analysis
                            │
                            ▼
                 Optimization Engine
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
        Recommendations             What-If Engine
                                          │
                                          ▼
                                  Before / After
                                          │
                                          ▼
                                   Merchant Action
                                          │
                                          ▼
                                  P0 Commerce Layer
                                          │
                                          ▼
                                       Razorpay
```

---

# 64. Final Engineering Principle

The P1 system should follow this exact separation:

```text
                 ┌──────────────────────┐
                 │         LLM          │
                 │                      │
                 │ Understand           │
                 │ Explain              │
                 │ Suggest              │
                 └──────────┬───────────┘
                            │
                     Structured Output
                            │
                            ▼
                 ┌──────────────────────┐
                 │ DETERMINISTIC LOGIC  │
                 │                      │
                 │ Filter               │
                 │ Score                │
                 │ Simulate             │
                 │ Validate             │
                 │ Calculate            │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ MERCHANT DECISION    │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │      P0 SYSTEM       │
                 │                      │
                 │ Policy               │
                 │ Authorization        │
                 │ Razorpay             │
                 │ Payment              │
                 └──────────────────────┘
```

**P1 should make the product smarter, more explainable, and more useful to merchants — without taking control away from deterministic business logic or the merchant.**
