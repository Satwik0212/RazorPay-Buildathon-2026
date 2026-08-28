# API Contracts & API Plan

**Project:** Razorpay AI Buildathon 2026 — Track 01: AI Growth & Agentic Commerce  
**Current product:** AI Buyer Simulation + Merchant Optimization + Razorpay transaction layer  
**Backend:** FastAPI  
**Database:** PostgreSQL + SQLAlchemy  
**Validation:** Pydantic v2  
**External payment provider:** Razorpay Test Mode

---

# 1. Purpose

This document defines the API surface of the entire application.

It answers:

- Which APIs exist?
- Who can call them?
- What does each API do?
- What request does it accept?
- What response does it return?
- Which APIs are P0/P1/P2?
- Which APIs are internal vs public?
- Where does validation happen?
- Where does AI participate?
- Which APIs can affect money?
- Which APIs must be idempotent?
- How do our APIs connect to Razorpay?

The API architecture follows:

```text
Frontend / AI Agent
        ↓
FastAPI API
        ↓
Pydantic validation
        ↓
Authentication / Authorization
        ↓
Service Layer
        ↓
Business Rules
        ↓
Database / AI / Razorpay
```

---

# 2. API Design Principles

## 2.1 The frontend never owns financial truth

The frontend can request:

```text
"Create a quote"
"Start checkout"
"Create payment order"
```

It must NOT decide:

```text
final amount
payment status
authorization
order paid status
```

---

## 2.2 AI never directly calls financial APIs

AI can call controlled application tools.

Example:

```text
AI Agent
   ↓
search_catalogue()
   ↓
recommend_products()
   ↓
create_simulation()
```

But:

```text
AI
  X
  ↓
Razorpay API directly
```

is prohibited.

Financial actions go through deterministic services.

---

## 2.3 Every endpoint has one clear responsibility

Avoid endpoints such as:

```text
POST /do-everything
```

Prefer:

```text
POST /quotes
POST /authorizations
POST /checkout/orders
POST /simulations
POST /optimizations
```

---

# 3. API Versioning

Base URL:

```text
/api/v1/v1
```

Example:

```text
GET /api/v1/products
```

External Razorpay calls are separate:

```text
https://api.razorpay.com/v1/...
```

Razorpay documents its REST API with `/v1` as the gateway base for most APIs. citeturn0search2

---

# 4. Authentication

Recommended mechanism:

```text
JWT access token
```

Flow:

```text
Login
 ↓
JWT
 ↓
Authorization: Bearer <token>
 ↓
FastAPI dependency
 ↓
Authenticated user
```

For the hackathon, JWT is sufficient.

---

# 5. Authentication APIs

## POST /api/v1/auth/register

### Purpose

Create a customer or merchant account.

### Request

```json
{
  "email": "merchant@example.com",
  "password": "strong-password",
  "role": "MERCHANT"
}
```

### Response

```json
{
  "user": {
    "id": "uuid",
    "email": "merchant@example.com",
    "role": "MERCHANT"
  },
  "access_token": "jwt",
  "token_type": "bearer"
}
```

### Validation

```text
email valid
password length >= 8
role from enum
```

---

# 6. POST /api/v1/auth/login

### Purpose

Authenticate a user.

### Request

```json
{
  "email": "merchant@example.com",
  "password": "strong-password"
}
```

### Response

```json
{
  "access_token": "jwt",
  "token_type": "bearer"
}
```

---

# 7. GET /api/v1/auth/me

### Purpose

Return the authenticated user.

### Response

```json
{
  "id": "uuid",
  "email": "merchant@example.com",
  "role": "MERCHANT"
}
```

---

# 8. Merchant APIs

## POST /api/v1/merchants

Create merchant profile.

### Request

```json
{
  "name": "Tech Store",
  "description": "Consumer electronics"
}
```

### Response

```json
{
  "id": "uuid",
  "name": "Tech Store",
  "description": "Consumer electronics",
  "is_active": true
}
```

---

# 9. GET /api/v1/merchants/me

Return current merchant profile.

Authorization:

```text
MERCHANT
```

---

# 10. PATCH /api/v1/merchants/me

Update merchant profile.

### Request

```json
{
  "name": "Tech Store India",
  "description": "Electronics and accessories"
}
```

---

# 11. Product APIs

These APIs form the merchant catalogue.

---

## POST /api/v1/products

### Purpose

Create a product.

### Request

```json
{
  "name": "Wireless ANC Headphones",
  "description": "Over-ear headphones with ANC",
  "category": "headphones",
  "price": 499900,
  "currency": "INR",
  "metadata": {
    "anc": true,
    "battery_hours": 30,
    "color": "black"
  }
}
```

### Important

`price` is in minor currency units.

For ₹4,999:

```text
499900
```

Razorpay's Order API likewise represents amounts in currency subunits. citeturn0search3turn0search11

---

# 12. GET /api/v1/products

### Purpose

Search/browse catalogue.

Query parameters:

```text
category
min_price
max_price
is_active
search
limit
offset
```

Example:

```text
GET /api/v1/products?category=headphones&max_price=500000
```

---

# 13. GET /api/v1/products/{product_id}

Return product details.

Ownership is checked where merchant-private data is involved.

---

# 14. PATCH /api/v1/products/{product_id}

Update a product.

### Request

```json
{
  "name": "Wireless ANC Headphones Pro",
  "price": 549900
}
```

Only the owning merchant can update it.

---

# 15. DELETE /api/v1/products/{product_id}

Recommended behavior:

```text
soft deactivate
```

rather than destroying historical product references.

---

# 16. POST /api/v1/products/bulk

### Purpose

Import multiple products for demo/testing.

### Request

```json
{
  "products": [
    {
      "name": "Product A",
      "category": "headphones",
      "price": 299900,
      "currency": "INR"
    }
  ]
}
```

Response:

```json
{
  "created": 1,
  "failed": 0,
  "errors": []
}
```

Useful for:

```text
merchant onboarding
demo setup
synthetic catalogue
```

---

# 17. Inventory APIs

## GET /api/v1/products/{product_id}/inventory

Return inventory.

```json
{
  "product_id": "uuid",
  "available_quantity": 20,
  "reserved_quantity": 2
}
```

---

# 18. PATCH /api/v1/products/{product_id}/inventory

Update inventory.

### Request

```json
{
  "available_quantity": 20
}
```

The service must enforce:

```text
quantity >= 0
```

---

# 19. Buyer Intent APIs

These are primarily P1.

## POST /api/v1/buyer/intents

### Purpose

Convert natural-language buyer intent into structured data.

### Request

```json
{
  "text": "I need ANC headphones under 5000 with delivery in 2 days"
}
```

### Response

```json
{
  "intent_id": "uuid",
  "intent": {
    "category": "headphones",
    "max_budget": 500000,
    "requirements": [
      "ANC"
    ],
    "delivery_deadline_days": 2
  }
}
```

Important:

```text
LLM → structured output → Pydantic → business validation
```

---

# 20. GET /api/v1/buyer/intents/{intent_id}

Return structured intent.

---

# 21. Catalogue Search API

## POST /api/v1/catalogue/search

### Purpose

Provide a structured search layer for the buyer/AI.

### Request

```json
{
  "category": "headphones",
  "max_budget": 500000,
  "requirements": ["ANC"],
  "preferences": ["long battery life"]
}
```

### Response

```json
{
  "results": [
    {
      "product_id": "uuid",
      "match_score": 0.94,
      "matched_constraints": [
        "ANC",
        "budget"
      ],
      "failed_constraints": []
    }
  ]
}
```

This is an important AI tool endpoint.

---

# 22. Cart APIs

## POST /api/v1/carts

Create a cart.

### Request

```json
{
  "merchant_id": "uuid"
}
```

### Response

```json
{
  "id": "uuid",
  "status": "ACTIVE"
}
```

---

# 23. GET /api/v1/carts/{cart_id}

Return cart contents.

Authorization:

```text
authenticated customer owns cart
```

---

# 24. POST /api/v1/carts/{cart_id}/items

Add item.

### Request

```json
{
  "product_id": "uuid",
  "quantity": 1
}
```

Validation:

```text
quantity > 0
product active
product belongs to merchant
inventory sufficient
```

---

# 25. PATCH /api/v1/carts/{cart_id}/items/{item_id}

Change quantity.

---

# 26. DELETE /api/v1/carts/{cart_id}/items/{item_id}

Remove item.

---

# 27. POST /api/v1/carts/{cart_id}/validate

### Purpose

Check whether the cart can proceed to checkout.

Checks:

```text
products active
inventory available
prices current
merchant active
cart valid
```

Response:

```json
{
  "valid": true,
  "issues": []
}
```

---

# 28. Quote APIs

## POST /api/v1/quotes

### Purpose

Create an authoritative server-side quote.

### Request

```json
{
  "cart_id": "uuid"
}
```

The client does NOT send:

```text
final_amount
```

The backend calculates it.

### Response

```json
{
  "quote_id": "uuid",
  "subtotal": 499900,
  "discount": 0,
  "shipping": 0,
  "tax": 0,
  "total": 499900,
  "currency": "INR",
  "expires_at": "2026-08-28T12:00:00Z"
}
```

---

# 29. GET /api/v1/quotes/{quote_id}

Return quote.

---

# 30. POST /api/v1/quotes/{quote_id}/validate

Check whether quote is still valid.

```json
{
  "valid": true,
  "expired": false,
  "amount": 499900,
  "currency": "INR"
}
```

---

# 31. Authorization APIs

## POST /api/v1/authorizations

### Purpose

Request authorization to proceed with a transaction.

### Request

```json
{
  "quote_id": "uuid"
}
```

The server derives:

```text
customer
merchant
amount
policy
```

### Response

```json
{
  "authorization_id": "uuid",
  "status": "APPROVED",
  "amount": 499900,
  "currency": "INR"
}
```

Possible statuses:

```text
APPROVED
REVIEW_REQUIRED
BLOCKED
EXPIRED
```

---

# 32. GET /api/v1/authorizations/{authorization_id}

Return authorization state.

---

# 33. Policy APIs

## GET /api/v1/merchant/policy

Return current merchant AI/payment policy.

---

# 34. PUT /api/v1/merchant/policy

### Request

```json
{
  "max_autonomous_amount": 500000,
  "daily_autonomous_limit": 5000000,
  "require_approval_above": 500000,
  "blocked_categories": [],
  "is_ai_enabled": true
}
```

This is merchant-controlled governance.

---

# 35. Checkout APIs

## POST /api/v1/checkout/orders

### Purpose

Create our local order and corresponding Razorpay Order.

Flow:

```text
quote
 ↓
validate
 ↓
authorization
 ↓
local order
 ↓
Razorpay order
 ↓
save razorpay_order_id
 ↓
return checkout information
```

### Request

```json
{
  "quote_id": "uuid",
  "authorization_id": "uuid"
}
```

### Response

```json
{
  "order_id": "uuid",
  "razorpay_order_id": "order_xxx",
  "amount": 499900,
  "currency": "INR",
  "status": "CREATED"
}
```

> **Idempotency REQUIRED:** The order creation flow MUST protect against double clicks, network retries, agent retries, and concurrent requests. This is achieved via a database-level `UNIQUE` constraint on `authorization_id` (so an authorization can only ever create one order) combined with API-level Idempotency-Key support.

Razorpay's official Orders API uses `POST /v1/orders` and requires amount/currency; the created order then links to subsequent payment activity. citeturn0search0turn0search3

---

# 36. Important Checkout Rule

The backend must calculate:

```text
Razorpay order amount
=
local order amount
=
authorization amount
=
quote total
```

If these do not match:

```text
STOP
```

---

# 37. GET /api/v1/checkout/orders/{order_id}

Return local order + checkout state.

---

# 38. GET /api/v1/checkout/orders/{order_id}/payments

Return local payment attempts.

The backend can also use Razorpay's order-payment API when reconciliation requires it. Razorpay exposes `GET /v1/orders/:id/payments` for payments associated with an order. citeturn0search4

---

# 39. Payment APIs

## GET /api/v1/payments/{payment_id}

Return our local payment record.

---

# 40. GET /api/v1/orders/{order_id}/payment-status

### Purpose

Return the authoritative local payment state to the frontend.

Response:

```json
{
  "order_id": "uuid",
  "status": "PAID",
  "payment_id": "uuid"
}
```

The browser's success callback must not itself be treated as authoritative payment confirmation.

Razorpay recommends webhooks for server-side event notification and API verification where an immediate critical status check is needed. citeturn0search16

---

# 41. Razorpay API Adapter

We should isolate Razorpay calls in:

```text
services/razorpay/
```

Example:

```text
razorpay_client.py
```

Methods:

```python
create_order()
fetch_order()
fetch_payment()
fetch_order_payments()
capture_payment()
```

Not every method needs to be used in P0.

Razorpay's Payments API can retrieve payment details and, where applicable, change an authorized payment to captured; it is not the mechanism for collecting the customer's payment itself. citeturn0search1turn0search5

---

# 42. External Razorpay API Contract

## POST https://api.razorpay.com/v1/orders

Request:

```json
{
  "amount": 499900,
  "currency": "INR",
  "receipt": "receipt_uuid",
  "notes": {
    "local_order_id": "uuid"
  }
}
```

Authentication:

```text
Razorpay Key ID + Key Secret
```

The Key Secret stays server-side.

Razorpay's quickstart specifies separate Test and Live keys and says the secret is shown only when generated. citeturn0search12

---

# 43. Razorpay Payment Fetch

## GET /v1/payments/{payment_id}

Used when:

```text
we need server-side verification/reconciliation
```

Never expose the Razorpay secret to the frontend.

---

# 44. Razorpay Order Fetch

## GET /v1/orders/{order_id}

Used for:

```text
reconciliation
debugging
payment-state verification
```

---

# 45. Razorpay Order Payments

## GET /v1/orders/{order_id}/payments

Used to retrieve payments associated with an order.

Razorpay documents this endpoint as returning authorised or failed payments for the order. citeturn0search4

---

# 46. Razorpay Webhook API

## POST /api/v1/webhooks/razorpay

This is NOT called by our frontend.

It is called by Razorpay.

Flow:

```text
Razorpay
 ↓
POST webhook
 ↓
raw request body
 ↓
signature verification
 ↓
event ID/idempotency
 ↓
business event processing
 ↓
database update
 ↓
audit
```

Razorpay documents webhooks as asynchronous server-to-server notifications and recommends them for automation. citeturn0search16

---

# 47. Webhook Events We Care About

Initial set:

```text
payment.authorized
payment.captured
payment.failed
order.paid
```

Potentially:

```text
payment.downtime.updated
```

if we build payment-downtime intelligence later.

Razorpay documents `payment.captured` and `order.paid` as corresponding to a captured payment/order state. citeturn0search13turn0search15

---

# 48. Webhook Security

The endpoint must:

```text
read raw body
verify Razorpay signature
reject invalid signatures
deduplicate events
validate event state
write audit event
```

Razorpay specifically warns that webhook signature verification must use the raw webhook request body rather than a parsed/cast representation. citeturn0search13turn0search15

---

# 49. Webhook Idempotency

Database:

```text
webhook_events.event_id UNIQUE
```

Flow:

```text
event received
 ↓
event_id exists?
 ├── YES → no-op
 └── NO
      ↓
   process
      ↓
   mark processed
```

This prevents duplicate webhook processing.

---

# 50. Buyer Simulation APIs

These are the core P1 APIs.

---

## POST /api/v1/optimization/simulations

### Purpose

Create an AI buyer simulation.

### Request

```json
{
  "merchant_id": "uuid",
  "scenario_count": 100,
  "buyer_profiles": [
    "BUDGET",
    "QUALITY",
    "SPEED",
    "COMPATIBILITY"
  ]
}
```

### Response

```json
{
  "simulation_id": "uuid",
  "status": "COMPLETED",
  "scenario_count": 100,
  "results": { ... }
}
```

> **Hackathon Note:** For the Buildathon, simulation runs synchronously in-process and returns a complete result on the same request. The QUEUED / RUNNING async lifecycle is P2 (future) and only needed if batch scenario counts grow large enough to cause HTTP timeouts.

---

# 51. GET /api/v1/optimization/simulations/{simulation_id}

Return simulation state.

```json
{
  "simulation_id": "uuid",
  "status": "COMPLETED",
  "scenario_count": 100,
  "completed": 100
}
```

Statuses:

```text
COMPLETED
FAILED
CANCELLED
```

---

# 52. GET /api/v1/optimization/simulations/{simulation_id}/summary

Return high-level results.

Example:

```json
{
  "buyers_simulated": 1000,
  "successful_matches": 742,
  "failed_matches": 258,
  "constraint_satisfaction_rate": 0.742,
  "average_decision_time_ms": 1240
}
```

---

# 53. GET /api/v1/optimization/simulations/{simulation_id}/scenarios

Return scenario-level results.

Query:

```text
limit
offset
profile
status
```

---

# 54. [P2/Future] POST /api/v1/optimization/simulations/{simulation_id}/run

Start execution.

Useful if simulation creation and execution are separated (P2 Async Lifecycle).

Response:

```json
{
  "simulation_id": "uuid",
  "status": "QUEUED"
}
```

Should be idempotent:

```text
QUEUED → no duplicate execution
COMPLETED → no-op / already complete
```

---

# 55. Buyer Persona APIs

## POST /api/v1/buyer-personas

Create persona.

### Request

```json
{
  "name": "Budget Buyer",
  "budget_min": 200000,
  "budget_max": 500000,
  "priorities": [
    "price",
    "value"
  ],
  "urgency": "MEDIUM"
}
```

---

# 56. GET /api/v1/buyer-personas

List personas.

---

# 57. GET /api/v1/buyer-personas/{persona_id}

Return persona.

---

# 58. PATCH /api/v1/buyer-personas/{persona_id}

Update persona.

---

# 59. Simulation Scenario API

## POST /api/v1/optimization/simulations/{simulation_id}/scenarios

Create a controlled scenario.

### Request

```json
{
  "persona_id": "uuid",
  "intent": {
    "category": "headphones",
    "max_budget": 500000,
    "requirements": ["ANC"]
  }
}
```

---

# 60. Scenario Result

Example:

```json
{
  "scenario_id": "uuid",
  "matched": false,
  "reason_codes": [
    "DELIVERY_UNKNOWN"
  ],
  "products_considered": 8,
  "selected_product_id": null
}
```

This structured output is more useful than storing only a natural-language LLM response.

---

# 61. Friction APIs

## GET /api/v1/optimization/simulations/{simulation_id}/frictions

Return detected friction.

Example:

```json
{
  "frictions": [
    {
      "type": "MISSING_ATTRIBUTE",
      "product_id": "uuid",
      "field": "delivery_days",
      "frequency": 183,
      "severity": "HIGH"
    }
  ]
}
```

---

# 62. Optimization APIs

These are P1.

## POST /api/v1/optimizations

### Purpose

Generate merchant optimization recommendations from simulation results.

### Request

```json
{
  "simulation_id": "uuid"
}
```

### Response

```json
{
  "simulation_run_id": "uuid",
  "status": "COMPLETED"
}
```

---

# 63. GET /api/v1/optimizations

List recommendations.

Filters:

```text
status
type
severity
product_id
```

---

# 64. GET /api/v1/optimizations/{optimization_id}

Return recommendation.

Example:

```json
{
  "id": "uuid",
  "type": "CATALOGUE_ATTRIBUTE",
  "title": "Add delivery-time information",
  "reason": "18.3% of simulated buyers rejected products because delivery information was unavailable.",
  "expected_simulated_impact": 0.12,
  "confidence": 0.86,
  "status": "PROPOSED"
}
```

---

# 65. POST /api/v1/optimizations/{optimization_id}/approve

Merchant approves recommendation.

Important:

```text
AI proposes.
Merchant approves.
```

For high-impact changes.

---

# 66. POST /api/v1/optimizations/{optimization_id}/reject

Merchant rejects recommendation.

Request:

```json
{
  "reason": "Not appropriate for current campaign"
}
```

---

# 67. POST /api/v1/optimizations/{optimization_id}/apply

Apply an approved deterministic change.

This endpoint must verify:

```text
optimization exists
merchant owns it
status = APPROVED
change is allowed
```

The LLM itself does not directly mutate the database.

---

# 68. What-If APIs

## POST /api/v1/optimizations/what-if

### Purpose

Test a proposed change without changing production data.

### Request

```json
{
  "simulation_id": "uuid",
  "changes": [
    {
      "product_id": "uuid",
      "field": "delivery_days",
      "new_value": 2
    }
  ]
}
```

### Response

```json
{
  "baseline_score": 0.62,
  "simulated_score": 0.78,
  "delta": 0.16
}
```

This is one of the most important demo APIs.

---

# 69. Experiment APIs

Optional P2.

## POST /api/v1/experiments

Create experiment.

---

# 70. GET /api/v1/experiments

List experiments.

---

# 71. GET /api/v1/experiments/{experiment_id}

Return experiment state/results.

---

# 72. POST /api/v1/experiments/{experiment_id}/start

Start experiment.

---

# 73. POST /api/v1/experiments/{experiment_id}/stop

Stop experiment.

---

# 74. Offer APIs — P2

## POST /api/v1/offers

Create AI-generated offer proposal.

---

# 75. GET /api/v1/offers

List offers.

---

# 76. POST /api/v1/offers/{offer_id}/approve

Merchant approves.

---

# 77. Campaign APIs — P2

## POST /api/v1/campaigns

Create campaign.

---

# 78. GET /api/v1/campaigns

List campaigns.

---

# 79. POST /api/v1/campaigns/{campaign_id}/simulate

Run campaign against simulated buyers.

---

# 80. POST /api/v1/campaigns/{campaign_id}/activate

Activate after approval.

---

# 81. Analytics APIs

## GET /api/v1/analytics/merchant/overview

Return:

```text
GMV
orders
conversion
AOV
simulation score
optimization impact
```

For the hackathon, simulation metrics should be clearly distinguished from real transaction metrics.

---

# 82. GET /api/v1/analytics/simulations

Return simulation trends.

Example:

```json
{
  "runs": 12,
  "average_constraint_satisfaction": 0.74,
  "latest": 0.81,
  "baseline": 0.61
}
```

---

# 83. GET /api/v1/analytics/optimizations

Return optimization impact.

Example:

```json
{
  "recommendations": 18,
  "approved": 7,
  "applied": 5,
  "simulated_improvement": 0.14
}
```

---

# 84. Audit APIs

## GET /api/v1/audit/events

Merchant/admin-only.

Filters:

```text
event_type
entity_type
entity_id
actor_id
start
end
```

Response:

```json
{
  "events": [
    {
      "event_type": "OPTIMIZATION_APPROVED",
      "entity_id": "uuid",
      "created_at": "..."
    }
  ]
}
```

---

# 85. Agent APIs

Agents should preferably use internal tools rather than unrestricted HTTP APIs.

But conceptually:

```text
Agent
 ↓
Tool Gateway
 ↓
Internal Service
```

Tools:

```text
search_catalogue
get_product
get_inventory
create_intent
run_simulation
get_simulation_results
get_optimization
request_optimization
create_cart
create_quote
request_authorization
```

---

# 86. Agent Tool: search_catalogue

Input:

```json
{
  "category": "headphones",
  "max_budget": 500000,
  "requirements": ["ANC"]
}
```

Output:

```json
{
  "products": [
    {
      "product_id": "uuid",
      "match_score": 0.94
    }
  ]
}
```

---

# 87. Agent Tool: get_product

Input:

```json
{
  "product_id": "uuid"
}
```

Output:

```json
{
  "id": "uuid",
  "name": "Wireless ANC Headphones",
  "price": 499900,
  "attributes": {}
}
```

---

# 88. Agent Tool: run_simulation

Input:

```json
{
  "merchant_id": "uuid",
  "scenario_count": 100
}
```

Output:

```json
{
  "simulation_id": "uuid",
  "status": ""
}
```

---

# 89. Agent Tool: request_optimization

Input:

```json
{
  "simulation_id": "uuid"
}
```

Output:

```json
{
  "simulation_run_id": "uuid"
}
```

---

# 90. Agent Tool: create_quote

Input:

```json
{
  "cart_id": "uuid"
}
```

Output:

```json
{
  "quote_id": "uuid",
  "total": 499900,
  "currency": "INR"
}
```

The agent does not supply:

```text
total
```

The backend calculates it.

---

# 91. Agent Tool: request_authorization

Input:

```json
{
  "quote_id": "uuid"
}
```

Output:

```json
{
  "authorization_id": "uuid",
  "status": "APPROVED"
}
```

---

# 92. Agent Tool: create_checkout_order

This should NOT be exposed to an unrestricted general-purpose agent.

If used:

```text
agent request
 ↓
policy
 ↓
authorization
 ↓
checkout service
 ↓
Razorpay
```

---

# 93. API Error Contract

All APIs should return consistent errors.

Example:

```json
{
  "error": {
    "code": "QUOTE_EXPIRED",
    "text": "The quote has expired.",
    "request_id": "req_123"
  }
}
```

---

# 94. Error Codes

Examples:

```text
AUTH_REQUIRED
FORBIDDEN
RESOURCE_NOT_FOUND
VALIDATION_ERROR
MERCHANT_ACCESS_DENIED
CART_NOT_FOUND
PRODUCT_INACTIVE
INSUFFICIENT_INVENTORY
QUOTE_EXPIRED
QUOTE_MISMATCH
AUTHORIZATION_BLOCKED
PAYMENT_VERIFICATION_FAILED
RAZORPAY_API_ERROR
WEBHOOK_SIGNATURE_INVALID
WEBHOOK_DUPLICATE
INVALID_STATE_TRANSITION
AI_OUTPUT_INVALID
SIMULATION_FAILED
OPTIMIZATION_NOT_APPROVED
```

---

# 95. HTTP Status Strategy

```text
200 OK
successful GET/update

201 Created
successful resource creation

202 Accepted
async job accepted

400 Bad Request
invalid request/business input

401 Unauthorized
missing/invalid authentication

403 Forbidden
authenticated but not allowed

404 Not Found
resource unavailable

409 Conflict
state/duplicate/concurrency conflict

422 Unprocessable Entity
Pydantic validation failure

429 Too Many Requests
rate limit

500 Internal Server Error
unexpected server error

502 Bad Gateway
external provider failure
```

---

# 96. Request IDs

Every request should have:

```text
X-Request-ID
```

If absent:

```text
backend generates one
```

Use it in:

```text
logs
audit
errors
Razorpay adapter logs
AI runs
```

This makes debugging much easier.

---

# 97. Idempotency

Critical POST endpoints should support:

```text
Idempotency-Key
```

Especially:

```text
POST /quotes
POST /authorizations
POST /checkout/orders
POST /optimizations
POST /simulations/{id}/run
```

Payment/order creation is particularly important.

---

# 98. Idempotency Flow

```text
Request
 ↓
Idempotency-Key
 ↓
already processed?
 ├── YES → return stored result
 └── NO
      ↓
    process
      ↓
    store result
```

---

# 99. API Rate Limits

Basic limits:

```text
Authentication:
5-10 requests/minute/IP

Simulation:
low concurrency per merchant

AI generation:
per-merchant quota

Catalogue:
reasonable burst limit

Checkout:
strict rate limit
```

Exact numbers can be configured later.

---

# 100. Async APIs

> **Hackathon Note:** During the Razorpay Buildathon, simulations run **synchronously in-process** and return complete results on the same request. Async background processing is not required.

Large AI operations that may become async at scale:

```text
POST /simulations/batch (only if scenario count is very large)
POST /optimizations (only for complex multi-product runs)
POST /experiments (P2)
```

If a job is truly async, the response returns:

```json
{
  "id": "uuid",
  "status": ""
}
```

Then:

```text
GET /simulations/{id}
```

---

# 101. Async Execution Architecture

```text
API
 ↓
Create job
 ↓
PostgreSQL
 ↓
Worker
 ↓
AI / simulation
 ↓
Store results
 ↓
status = COMPLETED
```

For the initial implementation, a simple worker/background mechanism is sufficient.

If scale becomes necessary:

```text
Redis + worker queue
```

can be introduced.

---

# 102. API → Database Mapping

| API Group | Main Tables |
|---|---|
| Auth | users |
| Merchant | merchants |
| Product | products |
| Inventory | inventory |
| Buyer | intents, customers |
| Cart | carts, cart_items |
| Quote | quotes |
| Policy | policies |
| Authorization | authorizations |
| Checkout | orders |
| Payment | payments |
| Webhook | webhook_events |
| Audit | audit_events |
| Simulation | buyer_personas, simulation_runs, simulation_results |
| Agent | agent_runs, agent_tool_calls |
| Optimization | optimization_recommendations, what_if_runs |
| Offers | offers |
| Campaigns | campaigns |
| Experiments | experiments |
| Analytics | events + aggregate queries |

---

# 103. API → AI Mapping

| API | AI Role |
|---|---|
| `/buyer/intents` | intent extraction |
| `/catalogue/search` | structured retrieval |
| `/simulations` | scenario generation/execution |
| `/frictions` | pattern analysis |
| `/optimizations` | recommendation generation |
| `/what-if` | simulation comparison |
| `/offers` | offer proposal |
| `/campaigns/*/simulate` | campaign simulation |

---

# 104. API → Razorpay Mapping

| Our API | Razorpay |
|---|---|
| `/checkout/orders` | `POST /v1/orders` |
| `/payments/{id}` | `GET /v1/payments/{id}` |
| `/checkout/orders/{id}/payments` | `GET /v1/orders/:id/payments` |
| `/payment-status` | Payment/Order fetch as needed |
| `/webhooks/razorpay` | Razorpay webhook events |

---

# 105. End-to-End Buyer Flow

```text
POST /buyer/intents
        ↓
POST /catalogue/search
        ↓
POST /carts
        ↓
POST /carts/{id}/items
        ↓
POST /quotes
        ↓
POST /authorizations
        ↓
POST /checkout/orders
        ↓
Razorpay Checkout
        ↓
Razorpay payment
        ↓
POST /webhooks/razorpay
        ↓
GET /orders/{id}/payment-status
```

---

# 106. End-to-End Merchant Intelligence Flow

```text
POST /simulations
        ↓
GET /simulations/{id}
        ↓
GET /simulations/{id}/frictions
        ↓
POST /optimizations
        ↓
GET /optimizations/{id}
        ↓
POST /optimizations/{id}/approve
        ↓
POST /optimizations/{id}/apply
        ↓
POST /optimizations/what-if
        ↓
GET /analytics/optimizations
```

---

# 107. API Security Boundaries

## Public/customer

```text
auth
buyer
catalogue
cart
quote
checkout
payment status
```

## Merchant

```text
products
inventory
simulations
optimizations
analytics
policy
audit
```

## Admin

```text
system health
global audit
platform controls
```

## Internal only

```text
Razorpay client
agent tools
worker endpoints
database operations
```

---

# 108. APIs That Can Affect Money

Strictly classify:

```text
POST /authorizations
POST /checkout/orders
POST /webhooks/razorpay
```

Potentially:

```text
payment capture
refunds
```

if added later.

These must have:

```text
authentication
authorization
validation
idempotency
audit
state transition checks
```

---

# 109. APIs That Must Never Trust AI

Never accept authoritative values from an LLM for:

```text
amount
currency
payment status
inventory quantity
authorization status
Razorpay payment ID
Razorpay order status
refund amount
```

AI can suggest.

Services decide.

---

# 110. OpenAPI

FastAPI should automatically generate:

```text
/api/v1/openapi.json
/docs
/redoc
```

The OpenAPI contract becomes the source of truth for frontend/backend integration.

---

# 111. Pydantic Request/Response Separation

For each important resource:

```text
CreateSchema
UpdateSchema
ResponseSchema
InternalSchema
```

Example:

```text
ProductCreate
ProductUpdate
ProductResponse
ProductInternal
```

Never return internal fields accidentally.

---

# 112. Example Pydantic API Contract

```python
class CreateQuoteRequest(BaseModel):
    cart_id: UUID


class QuoteResponse(BaseModel):
    id: UUID
    subtotal: int
    discount: int
    shipping: int
    tax: int
    total: int
    currency: str
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

Notice:

```text
client supplies cart_id
server calculates amount
```

---

# 113. Example FastAPI Endpoint

```python
@router.post(
    "/quotes",
    response_model=QuoteResponse,
    status_code=201,
)
async def create_quote(
    payload: CreateQuoteRequest,
    current_user: CurrentUser,
    service: QuoteService = Depends(get_quote_service),
):
    return await service.create_quote(
        customer_id=current_user.id,
        cart_id=payload.cart_id,
    )
```

The route remains thin.

---

# 114. API Service Boundary

```text
Route
  ↓
Service
  ↓
Repository
```

Example:

```text
QuoteRoute
   ↓
QuoteService
   ↓
CartRepository
ProductRepository
InventoryRepository
QuoteRepository
```

---

# 115. Razorpay Adapter Boundary

Do not put:

```python
requests.post("https://api.razorpay.com...")
```

inside a FastAPI route.

Use:

```text
CheckoutService
      ↓
RazorpayClient
      ↓
Razorpay API
```

This makes testing easier.

---

# 116. Razorpay Client Interface

Conceptually:

```python
class RazorpayClient:

    async def create_order(
        self,
        amount: int,
        currency: str,
        receipt: str,
        notes: dict,
    ):
        ...

    async def fetch_order(self, order_id: str):
        ...

    async def fetch_payment(self, payment_id: str):
        ...

    async def fetch_order_payments(self, order_id: str):
        ...
```

---

# 117. API Testing Strategy

Every important API gets:

```text
unit test
integration test
failure test
authorization test
```

Critical payment APIs additionally get:

```text
duplicate request test
invalid amount test
expired quote test
duplicate webhook test
invalid signature test
wrong merchant test
```

---

# 118. Simulation API Testing

Test:

```text
100 scenarios
1000 scenarios
invalid persona
missing catalogue field
empty catalogue
LLM malformed output
simulation timeout
duplicate execution
```

---

# 119. Optimization API Testing

Test:

```text
valid recommendation
invalid recommendation
merchant rejection
merchant approval
double approval
apply without approval
stale simulation
what-if without simulation
```

---

# 120. Payment API Testing

Test:

```text
successful payment
failed payment
duplicate webhook
out-of-order webhook
wrong amount
wrong order ID
expired quote
duplicate checkout request
Razorpay API timeout
Razorpay API error
```

---

# 121. Observability

Every API should log:

```text
request_id
user_id
merchant_id
endpoint
status_code
latency
error_code
```

For AI:

```text
agent_run_id
model
prompt_version
tool
latency
status
```

For payment:

```text
local_order_id
razorpay_order_id
payment_id
event_id
```

Never log:

```text
password
API secret
webhook secret
sensitive payment credentials
```

---

# 122. API Documentation Structure

The repository should eventually contain:

```text
docs/
└── api/
    ├── authentication.md
    ├── merchant.md
    ├── catalogue.md
    ├── buyer.md
    ├── cart.md
    ├── quote.md
    ├── authorization.md
    ├── checkout.md
    ├── payment.md
    ├── webhooks.md
    ├── simulation.md
    ├── optimization.md
    └── analytics.md
```

But for the hackathon, this single document + generated OpenAPI is enough.

---

# 123. P0 API List

Minimum APIs required to make the product functional:

```text
POST   /auth/register
POST   /auth/login
GET    /auth/me

POST   /merchants
GET    /merchants/me

POST   /products
GET    /products
GET    /products/{id}
PATCH  /products/{id}

GET    /products/{id}/inventory
PATCH  /products/{id}/inventory

POST   /carts
GET    /carts/{id}
POST   /carts/{id}/items
PATCH  /carts/{id}/items/{item_id}
DELETE /carts/{id}/items/{item_id}

POST   /carts/{id}/validate

POST   /quotes
GET    /quotes/{id}
POST   /quotes/{id}/validate

POST   /authorizations
GET    /authorizations/{id}

POST   /checkout/orders
GET    /checkout/orders/{id}

GET    /payments/{id}
GET    /orders/{id}/payment-status

POST   /webhooks/razorpay
```

---

# 124. P1 API List

Core intelligence:

```text
POST   /buyer/intents
GET    /buyer/intents/{id}

POST   /catalogue/search

POST   /buyer-personas
GET    /buyer-personas
GET    /buyer-personas/{id}
PATCH  /buyer-personas/{id}

POST   /simulations
GET    /simulations/{id}
POST   /simulations/{id}/run
GET    /simulations/{id}/summary
GET    /simulations/{id}/scenarios
POST   /simulations/{id}/scenarios
GET    /simulations/{id}/frictions

POST   /optimizations
GET    /optimizations
GET    /optimizations/{id}
POST   /optimizations/{id}/approve
POST   /optimizations/{id}/reject
POST   /optimizations/{id}/apply

POST   /optimizations/what-if

GET    /analytics/merchant/overview
GET    /analytics/simulations
GET    /analytics/optimizations

GET    /merchant/policy
PUT    /merchant/policy

GET    /audit/events
```

---

# 125. P2 API List

Optional:

```text
POST   /offers
GET    /offers
POST   /offers/{id}/approve

POST   /campaigns
GET    /campaigns
POST   /campaigns/{id}/simulate
POST   /campaigns/{id}/activate

POST   /experiments
GET    /experiments
GET    /experiments/{id}
POST   /experiments/{id}/start
POST   /experiments/{id}/stop
```

---

# 126. API Implementation Order

Do NOT implement APIs randomly.

Use this sequence:

```text
1. Auth
2. Merchant
3. Product
4. Inventory
5. Cart
6. Quote
7. Policy
8. Authorization
9. Checkout
10. Razorpay adapter
11. Webhook
12. Payment verification
13. Buyer intent
14. Catalogue search
15. Buyer personas
16. Simulation
17. Friction analysis
18. Optimization
19. What-if
20. Analytics
21. P2 features
```

---

# 127. The Critical P0 → P1 Boundary

P0 proves:

```text
"We can build a trustworthy commerce/payment system."
```

P1 proves:

```text
"We can add useful AI to it."
```

Both are necessary.

If P0 is missing:

```text
AI demo feels fake.
```

If P1 is missing:

```text
Razorpay has no reason to care about our AI.
```

---

# 128. The Most Important API Flow

The final demo should ideally exercise:

```text
Merchant login
     ↓
Catalogue
     ↓
Buyer simulation
     ↓
Friction
     ↓
Optimization
     ↓
Merchant approval
     ↓
Buyer checkout
     ↓
Quote
     ↓
Authorization
     ↓
Razorpay Order
     ↓
Payment
     ↓
Webhook
     ↓
Verified PAID state
     ↓
Audit
```

This connects the entire project.

---

# 129. API Contract Rules — Non-Negotiable

```text
1. All APIs versioned under /api/v1/v1.

2. Every request validated by Pydantic.

3. Every protected endpoint authenticates the caller.

4. Every merchant resource verifies merchant ownership.

5. Every customer resource verifies customer ownership.

6. Financial amounts are calculated server-side.

7. AI never directly mutates financial state.

8. Critical POST operations support idempotency.

9. Razorpay secrets never reach the frontend.

10. Payment state is not trusted from the browser.

11. Webhook signatures are verified using the raw body.

12. Webhook events are idempotently processed.

13. Financial state transitions are explicit.

14. Errors use a consistent structure.

15. Every request gets a request ID.

16. Important actions create audit records.

17. Simulations run synchronously in-process for the hackathon; introduce async only if timeout becomes a problem.

18. Simulation results are labelled as simulation.

19. Real transaction metrics and simulated metrics remain separate.

20. OpenAPI remains the machine-readable API contract.
```

---

# 130. Final API Architecture

```text
                         FRONTEND
                            │
                 ┌──────────┴──────────┐
                 │                     │
             Customer              Merchant
                 │                     │
                 └──────────┬──────────┘
                            ▼
                       FastAPI
                            │
                       /api/v1/v1
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
      Auth              Commerce            Intelligence
        │                   │                   │
        │              Product/Cart         Simulation
        │              Quote/Order         Optimization
        │              Checkout            Analytics
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                     Service Layer
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
         PostgreSQL        AI Layer     Razorpay
             │              │              │
             │              │              │
             ▼              ▼              ▼
           State         Reasoning      Payment
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                      Audit / Events
```

---

# 131. Final Mental Model

The API layer is not just a collection of URLs.

It is the **control boundary of the entire system**.

```text
Frontend asks.
AI proposes.
Services decide.
Database preserves state.
Razorpay executes payment.
Webhooks confirm external state.
Audit records what happened.
```

That is the API architecture we should build.

---

# 132. External Razorpay References

The following official Razorpay documentation should be treated as the source of truth when implementing the external integration because endpoint details and supported fields can change.

- Razorpay API Reference: https://razorpay.com/docs/api/v1/
- Orders API: https://razorpay.com/docs/api/v1/orders/
- Create Order: https://razorpay.com/docs/api/v1/orders/create/
- Payments API: https://razorpay.com/docs/api/v1/payments/
- Fetch Payments for an Order: https://razorpay.com/docs/api/v1/orders/fetch-payments/
- Webhooks: https://razorpay.com/docs/webhooks/
- Payment Webhook Events: https://razorpay.com/docs/webhooks/payments/
- Order Webhook Events: https://razorpay.com/docs/webhooks/orders/
- Quickstart: https://razorpay.com/docs/payments/quickstart/

Razorpay currently documents REST APIs returning JSON and uses `https://api.razorpay.com/v1` for most API resources. citeturn0search2

---

# 133. Final Implementation Rule

Do not start by implementing every endpoint in this document.

Build in vertical slices:

```text
SLICE 1
Auth → Merchant → Product

SLICE 2
Cart → Quote → Inventory

SLICE 3
Authorization → Razorpay Order → Payment

SLICE 4
Webhook → Verification → Audit

SLICE 5
Buyer Intent → Catalogue Search

SLICE 6
Simulation → Results → Friction

SLICE 7
Optimization → Approval → What-if

SLICE 8
Analytics → Final Demo
```

At the end of every slice:

```text
API works
+
DB works
+
validation works
+
frontend can consume it
+
failure case tested
```

This keeps the project demonstrable throughout development.
