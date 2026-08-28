# System Architecture — AI Commerce Platform

## 1. Architecture Overview

The system is a two-sided AI commerce platform connecting an **AI Buyer** with a **Merchant AI Control Center**, with Razorpay acting as the payment execution layer.

```text
                         CUSTOMER
                            │
                            ▼
                    ┌─────────────────┐
                    │  REACT FRONTEND │
                    │                 │
                    │ AI Buyer        │
                    │ Merchant UI     │
                    │ Policies        │
                    │ Analytics       │
                    └────────┬────────┘
                             │ HTTPS / JSON
                             ▼
              ┌──────────────────────────────┐
              │        FASTAPI BACKEND       │
              │                              │
              │ Auth → API → Services        │
              │        │                     │
              │   ┌────┼────┬────┐           │
              │   ▼    ▼    ▼    ▼           │
              │  AI  Commerce Governance     │
              │   │    │    │                │
              │   └────┼────┴────┘            │
              │        ▼                     │
              │   Payment Service             │
              └────┬────────┬──────────┬─────┘
                   │        │          │
                   ▼        ▼          ▼
              PostgreSQL   LLM      Razorpay
              Database   Provider      APIs
                                      │
                                      ▼
                                   Webhooks
```

---

# 2. Architectural Principles

### 2.1 AI proposes, backend decides

LLMs handle interpretation, reasoning, recommendations, and explanations.

They do **not** directly control money movement.

```text
User Request
    ↓
LLM
    ↓
Structured Proposal
    ↓
Deterministic Validation
    ↓
Policy / Authorization
    ↓
Execution
```

### 2.2 Server is the source of truth

The frontend never determines:

- final price
- payable amount
- authorization
- spending limits
- payment success
- transaction status

These are verified by the backend.

### 2.3 Payment execution is isolated

```text
Application
    ↓
PaymentService
    ↓
RazorpayAdapter
    ↓
Razorpay API
```

### 2.4 Financial actions are auditable

Important actions create audit events so that a transaction can be reconstructed later.

### 2.5 Complete the vertical transaction path first

```text
Intent
 → Product Discovery
 → Cart
 → Quote
 → Policy
 → Authorization
 → Razorpay Order
 → Checkout
 → Webhook
 → Transaction
 → Merchant Analytics
```

---

# 3. Actors and Roles

## Customer / AI Buyer

Can:

- submit natural-language intent
- discover products
- review recommendations
- manage cart
- initiate purchases
- approve payments when required
- view transaction status

## Merchant

Can:

- manage catalogue
- configure policies
- control agent permissions
- run AI-buyer simulations
- inspect AI-commerce readiness
- run optimizations
- view transactions
- inspect audit events

## AI Agents

Can:

- understand intent
- search and rank products
- propose carts
- explain decisions
- generate merchant insights
- propose optimization changes

AI agents cannot bypass deterministic backend controls.

---

# 4. Authentication & Authorization

## Authentication flow

```text
Signup / Login
      ↓
Auth API
      ↓
Credential Verification
      ↓
Access Token / Session
      ↓
Authenticated Request
      ↓
Load User
      ↓
Role + Ownership Check
      ↓
Endpoint
```

Passwords are stored only as strong password hashes.

## Role-based access

```text
Customer
 ├── Buyer endpoints ✓
 ├── Own carts ✓
 ├── Own transactions ✓
 └── Merchant settings ✕

Merchant
 ├── Own catalogue ✓
 ├── Own policies ✓
 ├── Own analytics ✓
 └── Other merchants' data ✕
```

Every protected resource must verify ownership on the server.

---

# 5. Backend Structure

```text
backend/
│
├── app/
│   ├── main.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── security.py
│   │
│   ├── api/
│   │   ├── auth.py
│   │   ├── buyer.py
│   │   ├── merchants.py
│   │   ├── catalog.py
│   │   ├── cart.py
│   │   ├── quote.py
│   │   ├── policies.py
│   │   ├── optimization.py
│   │   ├── analytics.py
│   │   ├── audit.py
│   │   └── webhooks.py
│   │
│   ├── agents/
│   │   ├── buyer_agent.py
│   │   ├── merchant_optimizer.py
│   │   └── prompts/
│   │
│   ├── commerce/
│   │   ├── catalog_service.py
│   │   ├── cart_service.py
│   │   ├── quote_service.py
│   │   └── offer_service.py
│   │
│   ├── governance/
│   │   ├── policy_engine.py
│   │   ├── authorization.py
│   │   └── risk.py
│   │
│   ├── optimization/
│   │   ├── simulator.py
│   │   ├── scorer.py
│   │   └── recommendations.py
│   │
│   ├── payments/
│   │   ├── service.py
│   │   ├── razorpay_adapter.py
│   │   └── webhook_service.py
│   │
│   ├── audit/
│   │   └── audit_service.py
│   │
│   ├── models/
│   ├── schemas/
│   └── db/
│       ├── database.py
│       └── repositories/
│
└── tests/
```

---

# 6. Database Architecture

PostgreSQL is the primary database.

```text
User
 │
 ├── Customer
 │     └── Intent
 │           └── Cart
 │                 └── Quote
 │                       └── Authorization
 │                             └── Order
 │                                   └── Payment
 │
 └── Merchant
       ├── Products
       │     └── Inventory
       ├── Policies
       ├── Offers
       └── Optimization Runs

All important actions
        ↓
    Audit Events
```

## Main tables

### users

- id
- email
- password_hash
- role
- created_at
- updated_at

### merchants

- id
- user_id
- name
- description
- created_at
- updated_at

### products

- id
- merchant_id
- name
- description
- category
- price
- currency
- active
- metadata
- created_at
- updated_at

### inventory

- id
- product_id
- available_quantity
- reserved_quantity
- updated_at

### policies

- id
- merchant_id
- max_autonomous_amount
- max_daily_amount
- allowed_categories
- blocked_categories
- human_approval_above
- autonomous_discount_limit
- created_at
- updated_at

### intents

- id
- customer_id
- raw_text
- structured_intent
- status
- created_at

### carts

- id
- customer_id
- merchant_id
- status
- created_at
- updated_at

### cart_items

- id
- cart_id
- product_id
- quantity

### quotes

- id
- cart_id
- subtotal
- discount
- tax
- shipping
- total
- currency
- expires_at
- quote_hash
- created_at

### authorizations

- id
- cart_id
- customer_id
- merchant_id
- requested_amount
- approved_amount
- status
- reason
- expires_at
- created_at

### orders

- id
- merchant_id
- customer_id
- cart_id
- razorpay_order_id
- amount
- currency
- status
- created_at
- updated_at

### payments

- id
- order_id
- razorpay_payment_id
- status
- method
- amount
- error_code
- error_reason
- created_at
- updated_at

### audit_events

- id
- actor_type
- actor_id
- event_type
- entity_type
- entity_id
- event_data
- created_at

---

# 7. AI Buyer Architecture

The AI Buyer is a controlled workflow, not an unrestricted LLM call.

```text
Natural Language
      ↓
Intent Parser
      ↓
Structured Intent
      ↓
Catalogue Search
      ↓
Deterministic Filtering
      ↓
AI Ranking
      ↓
Recommendation + Explanation
      ↓
Cart Proposal
```

Example:

```json
{
  "category": "headphones",
  "max_budget": 5000,
  "requirements": ["ANC"],
  "delivery_deadline": "3 days",
  "preferences": []
}
```

The backend validates this structure before using it.

## Product selection

```text
Catalogue
   ↓
Hard Filters
   ├── Active
   ├── Inventory
   ├── Price
   └── Explicit Constraints
   ↓
Candidate Products
   ↓
AI / Scoring Layer
   ↓
Ranked Products
```

The LLM never performs authoritative financial calculations.

---

# 8. Agent-Readable Catalogue

The catalogue service creates a consistent commerce representation.

```text
Merchant Data
     ↓
Normalization
     ↓
Validation
     ↓
Structured Commerce Schema
     ↓
AI Buyer / Simulator
```

A product can expose:

```text
Product
 ├── identity
 ├── description
 ├── category
 ├── price
 ├── currency
 ├── inventory
 ├── variants
 ├── delivery
 ├── returns
 ├── offers
 └── payment constraints
```

Incomplete or ambiguous information is flagged to the merchant.

---

# 9. Cart Architecture

The AI proposes a cart; the backend creates the authoritative cart.

```text
AI Cart Proposal
      ↓
Validate Products
      ↓
Check Inventory
      ↓
Check Current Price
      ↓
Create Cart
```

The frontend cannot set or modify the authoritative final price.

---

# 10. Deterministic Quote Engine

The quote engine calculates:

```text
Subtotal
   +
Shipping
   -
Discount
   +
Tax
   =
Final Total
```

Example:

```text
Products          ₹4,699
Shipping            ₹100
Discount            ₹200
-------------------------
Total              ₹4,599
```

Every quote has:

- unique ID
- cart reference
- amount
- currency
- expiry
- integrity/hash information

The Razorpay order amount is created from the verified server-side quote.

---

# 11. Merchant Policy Engine

Every autonomous financial action passes through the policy engine.

```text
Proposed Transaction
        ↓
Merchant Policy
        ↓
Amount Check
        ↓
Category Check
        ↓
Discount Check
        ↓
Approval Requirement
        ↓
ALLOW / REVIEW / BLOCK
```

Example:

```text
Cart = ₹7,500
Autonomous limit = ₹5,000

Result = REVIEW_REQUIRED
```

The AI cannot override the policy result.

---

# 12. Authorization

Authorization is separate from AI recommendation.

```text
AI Recommendation
      ↓
Cart
      ↓
Quote
      ↓
Policy Engine
      ↓
Authorization
```

Possible states:

```text
APPROVED
REVIEW_REQUIRED
BLOCKED
EXPIRED
```

For review:

```text
AI Proposal
    ↓
Policy
    ↓
REVIEW_REQUIRED
    ↓
Human Approval
    ↓
APPROVED
    ↓
Execution
```

Authorizations should expire so that stale approvals cannot be reused indefinitely.

---

# 13. AI Commerce Readiness

The readiness engine evaluates:

```text
Catalogue completeness
        +
Price clarity
        +
Inventory clarity
        +
Delivery clarity
        +
Return-policy clarity
        +
Offer clarity
        +
Transactionability
        ↓
AI Commerce Readiness Score
```

Example:

```text
Overall: 74/100

Product metadata      90
Pricing clarity       82
Inventory             95
Delivery information  60
Return information    55
Offers                70
```

The score is based on explicit checks and should always provide reasons.

---

# 14. AI Buyer Simulation

The simulator creates repeatable buyer scenarios.

```text
Buyer Persona
     +
Intent
     +
Constraints
     +
Merchant Catalogue
     ↓
Simulation Engine
     ↓
Product Ranking
     ↓
Selection / Rejection
     ↓
Reasons + Score
```

Example personas:

- Budget-focused
- Speed-focused
- Quality-focused
- Deal-focused
- Specification-focused

Each simulation records the scenario, candidates, ranking, result, reasons and score.

---

# 15. AI Commerce Optimizer

The optimizer sits above the simulator.

```text
Merchant Product
       ↓
Baseline Simulation
       ↓
Identify Weaknesses
       ↓
Generate Candidate Changes
       ↓
Run Simulations
       ↓
Compare Results
       ↓
Recommendation
```

Possible variables:

- price
- delivery information
- return-policy clarity
- offer structure
- product metadata
- inventory visibility

The optimizer must distinguish:

**Observed:** measured in the simulation.

**Projected:** outcome under a simulated change.

Simulation results must not be presented as guaranteed real-world revenue.

---

# 16. What-If Simulation

Example:

```text
CURRENT

Price: ₹5,499
Delivery: 4–6 days
Return: 7 days

AI Selection Score: 41
```

Merchant changes the simulation:

```text
Price: ₹5,199
Delivery: 2–3 days
Return: 30 days
```

The same buyer scenarios are run again.

```text
NEW

AI Selection Score: 58

Change: +17 points
```

The merchant decides whether to apply the real change. The optimizer must not silently modify merchant data.

---

# 17. Merchant Dashboard

Dashboard data comes from:

```text
Transactions
     +
Simulations
     +
Readiness
     +
Policies
     +
Optimization Runs
     +
Audit Events
```

Sections:

```text
Overview
 ├── AI Commerce Score
 ├── AI-assisted orders
 ├── AI transaction value
 └── Recent activity

AI Readiness
 ├── Score
 ├── Weaknesses
 └── Recommendations

Simulator
 ├── Buyer scenarios
 ├── Product selection
 └── Results

Optimizer
 ├── Current state
 ├── What-if changes
 └── Comparison

Policies
 ├── Spending limits
 ├── Categories
 └── Approval rules

Transactions
 ├── Orders
 ├── Payments
 └── Status

Audit
 └── Event timeline
```

---

# 18. Razorpay Integration

Razorpay integration is isolated behind a payment service.

```text
Application
     ↓
Payment Service
     ↓
Razorpay Adapter
     ↓
Razorpay API
```

## Create Order

```text
Authorization APPROVED
        ↓
Verified Quote
        ↓
Payment Service
        ↓
Razorpay Create Order
        ↓
razorpay_order_id
        ↓
Local Order Record
```

Secret Razorpay credentials remain server-side.

## Checkout

```text
Backend creates verified order
        ↓
Frontend receives checkout-safe data
        ↓
Razorpay Checkout
        ↓
Customer Payment
```

---

# 19. Razorpay Webhook

Webhook processing is asynchronous and must be idempotent.

```text
Razorpay
   ↓
POST /webhooks/razorpay
   ↓
Verify Signature
   ↓
Identify Event
   ↓
Idempotency Check
   ↓
Update Payment
   ↓
Update Order
   ↓
Create Audit Event
   ↓
Update Metrics
```

Example:

```text
Webhook #1 → process
Webhook #2 → detect duplicate → ignore/replay safely
```

---

# 20. Payment State Machine

Local payment state should explicitly represent the transaction lifecycle.

```text
CREATED
   ↓
ATTEMPTED
   ↓
AUTHORIZED
   ↓
CAPTURED
   ↓
COMPLETED
```

Failure branches:

```text
ATTEMPTED → FAILED

AUTHORIZED → EXPIRED / REFUNDED
```

Exact mapping to Razorpay events should follow the API/event semantics used during implementation.

---

# 21. Failure Handling

## Razorpay API timeout

```text
Request
  ↓
Timeout
  ↓
Do NOT blindly create another order
  ↓
Check existing state / idempotency
  ↓
Resolve
```

## Webhook failure

```text
Webhook
 ↓
Processing error
 ↓
Return appropriate response
 ↓
Razorpay retry
 ↓
Idempotent processing
```

## Payment failure

```text
Payment Failed
      ↓
Record failure
      ↓
Update Order
      ↓
Audit
      ↓
Merchant Analytics
```

The MVP should not automatically charge again after a payment failure.

---

# 22. Idempotency

Financial operations must be idempotent.

```text
Create Order
     ↓
idempotency_key = ABC123
     ↓
Existing result?
   ┌───┴───┐
  YES     NO
   │       │
Return   Execute
existing   │
result     ▼
        Store result
```

Apply the same principle to:

- order creation
- important payment actions
- webhook processing
- critical state transitions

---

# 23. Audit Trail

Every meaningful decision creates an audit event.

```text
INTENT_CREATED
      ↓
PRODUCTS_SELECTED
      ↓
CART_CREATED
      ↓
QUOTE_CREATED
      ↓
POLICY_CHECKED
      ↓
AUTHORIZATION_APPROVED
      ↓
RAZORPAY_ORDER_CREATED
      ↓
PAYMENT_ATTEMPTED
      ↓
PAYMENT_CAPTURED
      ↓
WEBHOOK_RECEIVED
      ↓
TRANSACTION_COMPLETED
```

Each event stores:

```text
event_id
actor
event_type
entity
entity_id
timestamp
metadata
```

This lets the merchant answer:

> "Why did this transaction happen?"

---

# 24. Security Architecture

## Secrets

```text
Environment / Secret Store
          ↓
Backend
```

Never expose:

- Razorpay secret
- LLM API key
- database credentials
- webhook signing secret

to React.

## Input validation

Every API request uses strict schemas.

## Authorization

Every resource access checks ownership.

## Webhooks

Verify signatures before processing.

## AI output

LLM output must be parsed and validated against strict schemas.

## Prompt injection

Customer and merchant content is untrusted input.

Product descriptions, user messages, and other external text must never be allowed to override system instructions or backend policies.

---

# 25. AI Safety Boundary

```text
                  AI
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
   Understand   Recommend    Explain
       │           │           │
       └───────────┼───────────┘
                   ▼
          Structured Output
                   ↓
        Deterministic Backend
                   ↓
        Policy + Authorization
                   ↓
               Execution
```

The AI cannot directly:

- change the authoritative payment amount
- bypass merchant policy
- authorize above a limit
- mark payments as successful
- modify Razorpay transaction state
- issue unrestricted refunds
- access another merchant's data

---

# 26. API Architecture

## Authentication

```text
POST /api/v1/auth/register
POST /api/v1/auth/login
GET  /api/v1/auth/me
```

## Buyer

```text
POST /api/v1/buyer/intents
POST /api/v1/buyer/search
POST /api/v1/buyer/cart
GET  /api/v1/buyer/cart/{id}
POST /api/v1/buyer/checkout
```

## Catalogue

```text
GET   /api/v1/catalog
POST  /api/v1/catalog/products
PATCH /api/v1/catalog/products/{id}
GET   /api/v1/catalog/products/{id}
```

## Policies

```text
GET /api/v1/merchant/policies
PUT /api/v1/merchant/policies
POST /api/v1/merchant/policies/check
```

## Quotes / Authorization

```text
POST /api/v1/quotes
GET  /api/v1/quotes/{id}
POST /api/v1/authorizations
GET  /api/v1/authorizations/{id}
```

## Optimization

```text
GET  /api/v1/optimization/readiness
POST /api/v1/optimization/simulations
POST /api/v1/optimization/what-if
GET  /api/v1/optimization/runs
```

## Payments

```text
POST /api/v1/payments/create-order
GET  /api/v1/payments/{id}
POST /api/v1/webhooks/razorpay
```

## Merchant

```text
GET /api/v1/merchant/dashboard
GET /api/v1/merchant/transactions
GET /api/v1/merchant/audit
```

---

# 27. Complete Purchase Execution

```text
Customer Intent
      ↓
AI Intent Parser
      ↓
Structured Intent
      ↓
Catalogue Search
      ↓
Deterministic Filters
      ↓
AI Ranking
      ↓
Product Recommendation
      ↓
Cart
      ↓
Server-Side Quote
      ↓
Merchant Policy
      ↓
Authorization
      ↓
Razorpay Order
      ↓
Razorpay Checkout
      ↓
Customer Payment
      ↓
Webhook
      ↓
Signature Verification
      ↓
Idempotency Check
      ↓
Payment Update
      ↓
Audit Event
      ↓
Merchant Metrics
```

---

# 28. Complete Merchant Optimization Flow

```text
Merchant Login
      ↓
Dashboard
      ↓
Select Product
      ↓
AI Commerce Readiness
      ↓
Generate Buyer Scenarios
      ↓
Run Baseline Simulation
      ↓
Identify Weaknesses
      ↓
Generate Improvements
      ↓
Merchant selects What-If
      ↓
Change Simulation Variable
      ↓
Re-run Same Scenarios
      ↓
Compare Baseline vs New Result
      ↓
Show Explanation
      ↓
Merchant Decision
```

---

# 29. End-to-End System Flow

```text
                    CUSTOMER
                       │
                       ▼
                  AI BUYER
                       │
               Intent + Search
                       │
                       ▼
              MERCHANT CATALOGUE
                       │
                       ▼
                     CART
                       │
                       ▼
              QUOTE + POLICY GATE
                       │
                 ┌─────┴─────┐
                 │           │
               BLOCK       APPROVE
                 │           │
                 │           ▼
                 │     AUTHORIZATION
                 │           │
                 │           ▼
                 │     RAZORPAY ORDER
                 │           │
                 │           ▼
                 │      RAZORPAY CHECKOUT
                 │           │
                 │           ▼
                 │        PAYMENT
                 │           │
                 │           ▼
                 │        WEBHOOK
                 │           │
                 │           ▼
                 │     AUDIT + METRICS
                 │           │
                 │           ▼
                 │   MERCHANT DASHBOARD
                 │           │
                 │           ▼
                 │    OPTIMIZATION LOOP
                 │           │
                 └───────────┘
```

---

# 30. Feedback Loop

```text
Merchant Catalogue
       ↓
AI Buyer sees catalogue
       ↓
AI evaluates products
       ↓
Purchase
       ↓
Razorpay Transaction
       ↓
Measurement
       ↓
Merchant Insights
       ↓
Optimization
       ↓
Improved Catalogue / Configuration
       ↓
AI Buyer Simulation
       ↓
Repeat
```

This creates the central **AI-commerce growth loop**.

---

# 31. Frontend Architecture

```text
frontend/
│
├── pages/
│   ├── Login
│   ├── Buyer
│   ├── Cart
│   ├── Checkout
│   ├── MerchantDashboard
│   ├── Readiness
│   ├── Simulator
│   ├── Optimizer
│   ├── Policies
│   ├── Transactions
│   └── Audit
│
├── components/
│   ├── AIChat
│   ├── ProductCard
│   ├── Cart
│   ├── PolicyGate
│   ├── ReadinessScore
│   ├── SimulationResults
│   ├── WhatIfPanel
│   ├── TransactionTimeline
│   └── AuditTimeline
│
├── services/
│   ├── api.ts
│   └── auth.ts
│
└── state/
    ├── auth
    ├── buyer
    └── merchant
```

---

# 32. Deployment Architecture

```text
                    INTERNET
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        React Frontend       Razorpay
             │
           HTTPS
             │
             ▼
        FastAPI Backend
          │    │    │
          │    │    └────→ LLM Provider
          │    │
          │    └─────────→ PostgreSQL
          │
          └──────────────→ Razorpay API
```

Recommended separation:

```text
Frontend → Static hosting / CDN
Backend  → Container / managed service
Database → Managed PostgreSQL
```

All communication should use HTTPS.

---

# 33. Testing Architecture

## Unit tests

Test:

- quote calculations
- policy engine
- authorization
- readiness scoring
- simulation scoring
- idempotency

## API tests

Test:

```text
auth
catalogue
cart
quote
policy
optimization
payments
webhooks
```

## Integration tests

Test:

```text
Intent
 ↓
Cart
 ↓
Quote
 ↓
Policy
 ↓
Order
```

and Razorpay Test Mode integration.

## End-to-end

Critical path:

```text
Login
 ↓
Buyer Intent
 ↓
Product Selection
 ↓
Cart
 ↓
Authorization
 ↓
Razorpay Checkout
 ↓
Test Payment
 ↓
Webhook
 ↓
Merchant Dashboard
```

---

# 34. Mandatory Edge Cases

```text
[ ] Invalid login
[ ] Unauthorized merchant access
[ ] Product out of stock
[ ] Product becomes inactive
[ ] Price changes before checkout
[ ] Quote expires
[ ] Cart changes after quote
[ ] Amount exceeds policy
[ ] Blocked category
[ ] Human approval required
[ ] Duplicate order request
[ ] Razorpay API timeout
[ ] Payment failure
[ ] Duplicate webhook
[ ] Invalid webhook signature
[ ] Unknown payment event
[ ] Invalid AI structured output
[ ] LLM unavailable
```

---

# 35. AI Failure / Fallback

If the LLM fails:

```text
AI Request
    ↓
LLM unavailable / Invalid Response
    ↓
Schema Validation Fails
    ↓
Fallback
```

For non-financial discovery, deterministic catalogue search can continue where possible.

For financial execution:

```text
AI unavailable
     ↓
No ambiguous autonomous financial decision
     ↓
Require normal user / merchant action
```

The system must fail safely rather than execute an uncertain financial action.

---

# 36. Observability

Track:

- API latency
- LLM latency
- LLM failures
- Razorpay API failures
- webhook failures
- policy decisions
- authorization outcomes
- payment states
- simulation runs

Useful correlation IDs:

```text
request_id
user_id
merchant_id
intent_id
cart_id
quote_id
authorization_id
order_id
payment_id
```

Never log secrets or unnecessary sensitive payment information.

---

# 37. Multi-Agent Development Boundaries

The implementation can be split across parallel coding agents without allowing them to modify the same core logic arbitrarily.

```text
Agent 1 — Backend / Commerce
 ├── FastAPI
 ├── DB
 ├── Catalogue
 ├── Cart
 ├── Quote
 └── Razorpay integration

Agent 2 — AI / Optimization
 ├── Intent parser
 ├── Buyer agent
 ├── Simulation
 ├── Readiness
 └── Optimizer

Agent 3 — Frontend
 ├── Buyer UI
 ├── Merchant dashboard
 ├── Policies
 ├── Simulator
 └── Analytics

Agent 4 — QA / Integration
 ├── Tests
 ├── Edge cases
 ├── Security
 ├── Razorpay flow
 └── Integration verification
```

Shared contracts must be defined first:

```text
API schemas
DB schema
AI output schemas
Policy schema
Payment states
```

---

# 38. Final Architecture

```text
                           ┌─────────────────┐
                           │    CUSTOMER     │
                           └────────┬────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │    AI BUYER     │
                           └────────┬────────┘
                                    │
                                    ▼
                    ┌────────────────────────────┐
                    │           FASTAPI          │
                    │                            │
                    │ Authentication             │
                    │ Intent / AI                │
                    │ Catalogue                  │
                    │ Cart                       │
                    │ Quote                      │
                    │ Policy Engine              │
                    │ Authorization              │
                    │ Optimization               │
                    │ Payment Service            │
                    │ Audit                      │
                    └───────┬──────────┬─────────┘
                            │          │
                ┌───────────┘          └────────────┐
                ▼                                   ▼
        ┌───────────────┐                   ┌───────────────┐
        │  PostgreSQL   │                   │   LLM         │
        │               │                   │   Provider     │
        │ Users         │                   │               │
        │ Merchants     │                   │ Intent        │
        │ Products      │                   │ Ranking       │
        │ Carts         │                   │ Explanation   │
        │ Orders        │                   │ Optimization  │
        │ Payments      │                   └───────────────┘
        │ Policies      │
        │ Simulations   │
        │ Audit         │
        └───────┬───────┘
                │
                │
                ▼
        ┌─────────────────┐
        │    RAZORPAY     │
        │                 │
        │ Orders          │
        │ Checkout        │
        │ Payments        │
        │ Webhooks        │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ MERCHANT CONTROL CENTER │
        │                         │
        │ AI Readiness            │
        │ Buyer Simulation        │
        │ Optimization            │
        │ Policies                │
        │ Transactions            │
        │ Audit                   │
        └─────────────────────────┘
```

---

# 39. Architectural North Star

The system must always preserve this boundary:

```text
             AI
              │
     Understand / Recommend
              │
              ▼
      Structured Proposal
              │
              ▼
      Deterministic Backend
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
   Quote    Policy   Authorization
      └───────┼────────┘
              ▼
          Razorpay
              ↓
           Payment
              ↓
          Webhook
              ↓
      Database + Audit
              ↓
     Merchant Intelligence
              ↓
        Optimization
```

**The product is not an LLM wrapped around Razorpay.**

It is a controlled commerce system where AI handles reasoning-heavy tasks, deterministic services handle correctness and authorization, and Razorpay handles payment execution.
