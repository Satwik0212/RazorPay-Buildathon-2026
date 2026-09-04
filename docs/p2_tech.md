# P2 Tech & Logic — AI Commerce Platform

> **Purpose:** P2 contains the advanced, future-facing capabilities built on top of the stable P0 + P1 system.
>
> P2 is optional. It should only be implemented after the complete P0 payment flow and P1 optimization loop are stable.

---

# 0. P2 Objective

P2 evolves the product from an AI-assisted commerce system into a controlled **AI commerce infrastructure layer**.

```text
P0
AI Buyer → Commerce → Razorpay Payment

P1
AI Buyer → Simulation → Merchant Optimization

P2
Multiple AI Agents
      ↓
Conversational Commerce
      ↓
Personalization
      ↓
Offers / Campaigns
      ↓
Continuous Optimization
      ↓
Measured Outcomes
```

The core rule never changes:

```text
AI proposes / reasons / orchestrates
        ↓
Deterministic services validate
        ↓
Policy + Risk + Authorization
        ↓
Execution
```

---

# 1. P2 Scope

1. Multi-Agent Commerce Orchestrator
2. Conversational Checkout
3. Personalized AI Buyer Memory
4. Upsell & Cross-Sell Agent
5. Campaign Orchestrator
6. Continuous Merchant Optimization
7. Experimentation
8. AI Commerce Event Stream
9. Advanced Risk / Trust Controls
10. Human-in-the-Loop Agent Controls
11. Agent Observability
12. Agent Evaluation

---

# 2. P2 Architecture

```text
                         CUSTOMER
                            │
                            ▼
                    Conversational UI
                            │
                            ▼
                  AI Commerce Orchestrator
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
        Buyer Agent    Offer Agent    Checkout Agent
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                   Governance Gateway
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
          Policy         Validation       Risk
             └──────────────┼──────────────┘
                            ▼
                     Commerce Services
                            │
                 ┌──────────┼──────────┐
                 ▼          ▼          ▼
              Cart       Quote      Inventory
                 │
                 ▼
              Payment
                 │
                 ▼
              Razorpay
                 │
                 ▼
              Webhooks
                 │
                 ▼
              Events
                 │
        ┌────────┴──────────┐
        ▼                   ▼
 Merchant Intelligence   Optimization
```

---

# 3. Technology Stack

P2 continues the P0/P1 stack.

## Frontend

- React
- TypeScript
- Tailwind CSS
- React Router
- Recharts

Optional:

- TanStack Query
- Server-Sent Events / WebSockets

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- PostgreSQL

## AI

- LLM provider adapter
- Structured outputs
- Versioned prompts
- Agent evaluation

## Optional infrastructure

Only introduce when necessary:

```text
Redis
Message queue
Background workers
Vector database
Object storage
```

Do not add infrastructure merely to make the architecture look complicated.

---

# 4. Agent Gateway

Agents must not call arbitrary backend functions.

```text
Agent
  ↓
Tool Registry
  ↓
Permission Check
  ↓
Input Validation
  ↓
Business Service
  ↓
Result
```

Example tools:

```text
search_products
get_product
create_cart
get_quote
check_policy
request_authorization
create_payment_order
get_transaction
recommend_offer
run_simulation
get_merchant_metrics
```

The tool registry becomes the security boundary for agent actions.

---

# 5. Tool Contract

Example:

```json
{
  "name": "search_products",
  "description": "Search merchant products using structured criteria.",
  "input_schema": {
    "category": "string",
    "max_budget": "integer",
    "requirements": ["string"]
  },
  "permission": "buyer"
}
```

Never allow an agent to submit arbitrary SQL, database operations, or raw Razorpay requests.

---

# 6. Multi-Agent Commerce Orchestrator

## Goal

Use specialized agents instead of one giant prompt.

```text
User
 ↓
Orchestrator
 ├── Buyer Agent
 ├── Product Agent
 ├── Offer Agent
 ├── Checkout Agent
 └── Merchant Agent
```

---

# 7. Agent Responsibilities

## Buyer Agent

```text
intent
preferences
product discovery
recommendation
```

## Product Agent

```text
catalogue interpretation
product comparison
attribute reasoning
```

## Offer Agent

```text
upsell
cross-sell
bundles
offer recommendations
```

## Checkout Agent

```text
cart
quote
payment preparation
checkout status
```

The Checkout Agent cannot directly authorize payment.

## Merchant Agent

```text
analytics
insights
optimization
campaign suggestions
```

---

# 8. Orchestrator Flow

```text
User message
     ↓
Intent classification
     ↓
Determine required capability
     ↓
Select agent
     ↓
Agent calls approved tools
     ↓
Tool results
     ↓
Agent response
     ↓
Orchestrator
     ↓
User
```

Complex flow:

```text
User
 ↓
Orchestrator
 ↓
Buyer Agent
 ↓
Offer Agent
 ↓
Checkout Agent
 ↓
Final response
```

---

# 9. Agent State

Conversation history is not the source of truth.

Store structured state:

```text
conversation_id
customer_id
merchant_id
intent_id
cart_id
quote_id
authorization_id
order_id
current_agent
state
```

Example:

```json
{
  "conversation_id": "conv_123",
  "intent_id": "intent_123",
  "cart_id": "cart_123",
  "state": "AWAITING_PAYMENT"
}
```

---

# 10. Agent State Machine

```text
DISCOVERY
    ↓
PRODUCT_SELECTED
    ↓
CART_READY
    ↓
QUOTE_READY
    ↓
AUTHORIZATION
    ↓
PAYMENT_READY
    ↓
PAYMENT
    ↓
COMPLETED
```

Interruptions:

```text
REVIEW_REQUIRED
PAYMENT_FAILED
QUOTE_EXPIRED
USER_CANCELLED
```

---

# 11. P2 Feature — Conversational Checkout

## Goal

Allow the customer to perform commerce actions through conversation.

Example:

```text
"Find me a laptop under ₹60k."
        ↓
"Here are three options."

"Take the second one."
        ↓
"Added to your cart."

"Checkout."
        ↓
Fresh quote → policy → authorization → payment
```

Chat is only another input mechanism. Backend commerce state remains authoritative.

---

# 12. Conversational Checkout API

```http
POST /api/v1/conversations/{conversation_id}/message
```

Request:

```json
{
  "message": "Add the second laptop and checkout"
}
```

Response:

```json
{
  "message": "The second laptop has been added.",
  "state": "CART_READY",
  "actions": [
    {
      "type": "CART_UPDATED"
    }
  ]
}
```

---

# 13. Conversational Action Safety

For:

```text
"Buy it."
```

the agent must not jump directly to payment.

```text
Buy intent
 ↓
Cart
 ↓
Fresh quote
 ↓
Policy
 ↓
Authorization
 ↓
Razorpay Checkout
```

Final financial execution remains behind deterministic gates.

---

# 14. P2 Feature — Personalized AI Buyer Memory

## Goal

Remember useful commerce preferences.

Example:

```text
frequently prefers:
- wireless products
- faster delivery
- mid-range pricing
- longer returns
```

---

# 15. Memory Architecture

Store structured preferences, not arbitrary permanent conversation history.

```text
Customer
 ├── preferred_categories
 ├── preferred_price_range
 ├── preferred_brands
 ├── delivery_preference
 └── feature_preferences
```

Preference object:

```json
{
  "key": "delivery_preference",
  "value": "fast",
  "confidence": 0.86,
  "source": "repeated_behavior"
}
```

One statement should not automatically become a permanent preference.

---

# 16. Memory API

```http
GET    /api/v1/customer/preferences
POST   /api/v1/customer/preferences
DELETE /api/v1/customer/preferences/{id}
```

Customers should be able to inspect and remove stored preferences.

---

# 17. Privacy Boundary

Store only commerce-relevant data.

```text
✓ preferred budget
✓ category preference
✓ delivery preference

✕ unnecessary personal information
✕ unrelated conversation history
```

---

# 18. P2 Feature — Upsell & Cross-Sell Agent

## Goal

Recommend relevant additions to the current purchase.

Example:

```text
Laptop
 ↓
Compatible bag
 ↓
Mouse
 ↓
Warranty
```

Avoid showing irrelevant or repetitive offers.

---

# 19. Product Relationship Model

```text
product_relationships

id
product_id
related_product_id
relationship_type
priority
metadata
```

Types:

```text
CROSS_SELL
UPSELL
ACCESSORY
BUNDLE
ALTERNATIVE
```

---

# 20. Upsell Pipeline

```text
Current Cart
     ↓
Product Relationships
     ↓
Candidate Add-ons
     ↓
Inventory Filter
     ↓
Policy Filter
     ↓
Relevance Score
     ↓
Offer
```

---

# 21. Offer Scoring

Example:

```text
score =
compatibility × 0.35
+
relevance × 0.30
+
price_fit × 0.15
+
merchant_priority × 0.10
+
inventory × 0.10
```

Hard constraints remain deterministic.

---

# 22. Offer API

```http
POST /api/v1/offers/recommend
```

Request:

```json
{
  "cart_id": "cart_123"
}
```

Response:

```json
{
  "offers": [
    {
      "product_id": "p_456",
      "type": "CROSS_SELL",
      "reason": "Compatible with the selected laptop.",
      "score": 0.88
    }
  ]
}
```

Track:

```text
shown
clicked
accepted
dismissed
```

---

# 23. P2 Feature — Campaign Orchestrator

## Goal

Allow merchants to provide a business objective and receive an AI-generated campaign plan.

Example:

> Increase headphone sales this weekend without discounting more than 10%.

Flow:

```text
Merchant Goal
 ↓
Catalogue + inventory + analytics
 ↓
AI strategy generation
 ↓
Structured campaign
 ↓
Validation
 ↓
Simulation
 ↓
Merchant approval
 ↓
Launch
```

---

# 24. Campaign Model

```text
campaigns

id
merchant_id
name
objective
status
start_at
end_at
budget
created_at
updated_at
```

```text
campaign_actions

id
campaign_id
type
configuration
status
created_at
```

Action types:

```text
OFFER
BUNDLE
UPSELL
PRODUCT_PRIORITY
AUDIENCE_TARGET
MESSAGE
```

---

# 25. Campaign API

```http
POST /api/v1/campaigns
GET  /api/v1/campaigns
GET  /api/v1/campaigns/{id}
POST /api/v1/campaigns/{id}/simulate
POST /api/v1/campaigns/{id}/approve
POST /api/v1/campaigns/{id}/pause
```

---

# 26. Campaign AI Boundary

The LLM proposes:

```text
campaign strategy
```

The backend validates:

```text
discount limit
budget
inventory
product state
merchant permissions
```

Only after merchant approval can a campaign become active.

---

# 27. P2 Feature — Continuous Merchant Optimization

P1:

```text
Merchant manually runs simulation.
```

P2:

```text
System continuously observes commerce signals.
```

Architecture:

```text
Commerce Events
      ↓
Event Aggregation
      ↓
Merchant Metrics
      ↓
Opportunity Detection
      ↓
AI Analysis
      ↓
Recommendation
      ↓
Merchant Notification
```

---

# 28. Opportunity Detection

Examples:

```text
Product repeatedly rejected
Delivery information repeatedly hurts ranking
Inventory frequently unavailable
Upsell accepted frequently
Specific buyer segment underperforms
```

Example:

```json
{
  "type": "OPPORTUNITY",
  "priority": "HIGH",
  "product_id": "p_123",
  "reason": "Speed-focused buyers frequently reject this product."
}
```

---

# 29. P2 Feature — Commerce Event Stream

Instead of tightly coupling components:

```text
Service
  ↓
Event
  ↓
Event Store
  ↓
Consumers
```

Events:

```text
product.created
product.updated
cart.created
quote.created
payment.created
payment.captured
payment.failed
simulation.completed
offer.shown
offer.clicked
offer.accepted
campaign.launched
```

---

# 30. Event Schema

```json
{
  "event_id": "evt_123",
  "event_type": "payment.captured",
  "timestamp": "...",
  "merchant_id": "m_123",
  "customer_id": "c_123",
  "entity_type": "payment",
  "entity_id": "pay_123",
  "metadata": {}
}
```

For P2 MVP:

```text
PostgreSQL events table
```

For larger scale:

```text
PostgreSQL
 ↓
Message Broker
 ↓
Consumers
```

Do not introduce Kafka unless genuinely required.

---

# 31. P2 Feature — Experimentation

Allow merchants to compare strategies.

Example:

```text
Variant A:
₹4,999

Variant B:
₹5,199 + free shipping
```

---

# 32. Experiment Model

```text
experiments

id
merchant_id
name
primary_metric
status
start_at
end_at
```

```text
experiment_variants

id
experiment_id
name
configuration
```

---

# 33. Experiment Flow

```text
Create Experiment
 ↓
Define Variants
 ↓
Validate
 ↓
Simulate
 ↓
Merchant Approval
 ↓
Launch
 ↓
Collect Events
 ↓
Compare
```

Always distinguish:

```text
SIMULATED IMPACT
```

from:

```text
OBSERVED REAL-WORLD IMPACT
```

---

# 34. P2 Feature — Risk / Trust Controls

More autonomous agents require stronger governance.

Signals:

```text
transaction amount
velocity
unusual quantity
repeated failures
policy boundary
agent behaviour
```

---

# 35. Risk Pipeline

```text
Transaction
     ↓
Risk Engine
     ↓
Signals
     ↓
Risk Score
     ↓
Policy
     ↓
ALLOW / REVIEW / BLOCK
```

Example:

```json
{
  "score": 0.72,
  "decision": "REVIEW",
  "reasons": [
    "Transaction exceeds typical amount."
  ]
}
```

Risk should be explainable.

---

# 36. P2 Feature — Human-in-the-Loop Controls

Merchant controls what each agent can do.

Example:

```text
Buyer Agent

✓ Search products
✓ Add to cart
✓ Request quote
✕ Approve above ₹5,000
✕ Modify merchant price
✕ Issue refund
```

---

# 37. Agent Permission Model

```text
agent_permissions

id
merchant_id
agent_type
tool_name
allowed
limit_config
created_at
updated_at
```

Example:

```json
{
  "agent_type": "buyer",
  "tool_name": "create_cart",
  "allowed": true
}
```

---

# 38. Permission Flow

```text
Agent
 ↓
Tool requested
 ↓
Permission lookup
 ↓
Allowed?
 ┌────┴────┐
 YES       NO
 ↓          ↓
Execute    Deny
```

For financial tools:

```text
Permission
 ↓
Limit
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Execute
```

---

# 39. P2 Feature — Agent Evaluation

Measure agent quality.

Metrics:

```text
intent accuracy
constraint satisfaction
product relevance
tool correctness
tool error rate
policy violations
checkout completion
explanation accuracy
```

---

# 40. Evaluation Pipeline

```text
Golden Scenarios
      ↓
Agent
      ↓
Output
      ↓
Evaluator
      ↓
Metrics
      ↓
Regression Report
```

Example:

```text
Intent Accuracy:          94%
Constraint Satisfaction:  98%
Product Relevance:        87%
Policy Violations:         0
```

---

# 41. Golden Test Cases

Maintain fixed scenarios:

```text
"Find headphones under ₹5k."
"Need something delivered tomorrow."
"Buy the cheapest option."
"Don't exceed ₹2k."
"Add a compatible mouse."
```

Store:

```text
scenario
expected intent
expected constraints
expected tool sequence
expected policy outcome
```

---

# 42. Prompt Versioning

Every agent execution should record:

```text
agent_name
prompt_version
model
tool_set
```

Example:

```json
{
  "agent": "buyer",
  "prompt_version": "buyer_v3",
  "model": "..."
}
```

This allows regression debugging.

---

# 43. P2 Vector Search

Optional.

Use vector search for:

```text
product descriptions
merchant FAQs
return-policy documents
semantic catalogue retrieval
```

Architecture:

```text
Knowledge
 ↓
Embedding
 ↓
Vector Store
 ↓
Retriever
 ↓
Agent Context
```

Never use vector search as the authoritative source for:

```text
price
inventory
payment state
policy state
transaction amount
```

Those remain in PostgreSQL/business services.

---

# 44. P2 Background Jobs

Long-running work:

```text
batch simulations
campaign analysis
agent evaluations
analytics aggregation
opportunity detection
```

Flow:

```text
API
 ↓
Create Job
 ↓
Worker
 ↓
Process
 ↓
Persist Result
 ↓
Frontend polls / receives update
```

For a small deployment, FastAPI background tasks may be enough.

---

# 45. P2 Real-Time UI

Optional:

```text
Backend
 ↓
SSE / WebSocket
 ↓
Dashboard
```

Example:

```text
Simulation started
 ↓
34/100
 ↓
67/100
 ↓
100/100
 ↓
Completed
```

Polling is acceptable if real-time streaming becomes a time sink.

---

# 46. P2 Merchant Dashboard

```text
Overview
 ├── Revenue
 ├── AI Commerce Score
 ├── AI-assisted orders
 └── Opportunities

AI Buyers
 ├── Personas
 ├── Conversations
 ├── Preferences
 └── Agent Performance

Optimization
 ├── Recommendations
 ├── What-If
 ├── Experiments
 └── Campaigns

Commerce
 ├── Products
 ├── Offers
 ├── Orders
 └── Payments

Governance
 ├── Policies
 ├── Agent Permissions
 ├── Risk
 └── Audit
```

---

# 47. P2 API Groups

## Agents

```http
POST /api/v1/agents/message
GET  /api/v1/agents
GET  /api/v1/agents/{id}
```

## Conversations

```http
POST /api/v1/conversations
POST /api/v1/conversations/{id}/message
GET  /api/v1/conversations/{id}
```

## Preferences

```http
GET    /api/v1/customer/preferences
POST   /api/v1/customer/preferences
DELETE /api/v1/customer/preferences/{id}
```

## Offers

```http
POST /api/v1/offers/recommend
GET  /api/v1/offers/history
POST /api/v1/offers/{id}/accept
POST /api/v1/offers/{id}/dismiss
```

## Campaigns

```http
POST /api/v1/campaigns
GET  /api/v1/campaigns
POST /api/v1/campaigns/{id}/simulate
POST /api/v1/campaigns/{id}/approve
POST /api/v1/campaigns/{id}/pause
```

## Experiments

```http
POST /api/v1/experiments
GET  /api/v1/experiments
POST /api/v1/experiments/{id}/simulate
POST /api/v1/experiments/{id}/launch
GET  /api/v1/experiments/{id}/results
```

## Risk

```http
POST /api/v1/risk/evaluate
GET  /api/v1/merchant/risk
```

## Agent permissions

```http
GET /api/v1/merchant/agent-permissions
PUT /api/v1/merchant/agent-permissions
```

## Evaluation

```http
POST /api/v1/evaluations/run
GET  /api/v1/evaluations/{id}
GET  /api/v1/evaluations/metrics
```

---

# 48. P2 Database Additions

## conversations

```text
id
customer_id
merchant_id
state
created_at
updated_at
```

## agent_runs

```text
id
conversation_id
agent_type
prompt_version
model
status
started_at
completed_at
```

## agent_tool_calls

```text
id
agent_run_id
tool_name
input_json
output_json
status
created_at
```

## customer_preferences

```text
id
customer_id
key
value
confidence
source
created_at
updated_at
```

## product_relationships

```text
id
product_id
related_product_id
relationship_type
priority
metadata
```

## offers

```text
id
merchant_id
product_id
cart_id
type
status
reason
created_at
```

## campaigns

```text
id
merchant_id
name
objective
status
start_at
end_at
created_at
```

## experiments

```text
id
merchant_id
name
primary_metric
status
created_at
```

## experiment_variants

```text
id
experiment_id
name
configuration
```

## events

```text
id
event_type
merchant_id
customer_id
entity_type
entity_id
metadata
created_at
```

## risk_evaluations

```text
id
transaction_id
score
decision
reasons
created_at
```

---

# 49. P2 Security Boundary

The more capable the agents become, the stricter the boundary must be.

```text
Agent
 ↓
Tool
 ↓
Permission
 ↓
Input Validation
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Execution
```

Never allow:

```text
LLM → SQL
LLM → Razorpay
LLM → arbitrary database mutation
LLM → payment state
```

---

# 50. Prompt Injection Defense

Treat all external content as untrusted:

```text
product descriptions
merchant text
customer messages
campaign text
retrieved documents
```

Retrieved content is data, not instructions.

---

# 51. P2 Payment Safety

Even with multiple agents:

```text
Agent
 ↓
"Pay ₹X"
 ↓
Fresh Quote
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Razorpay
```

Never:

```text
Agent → Razorpay API
```

---

# 52. P2 Idempotency

Agent retries make idempotency essential.

```text
Agent requests order
       ↓
Network timeout
       ↓
Agent retries
       ↓
Idempotency key
       ↓
Existing order returned
```

Possible key:

```text
conversation_id + action_id
```

or another unique operation identifier.

---

# 53. Agent Loop Protection

Every agent execution should have:

```text
timeout
max steps
max tool calls
max retries
```

Example:

```text
max_agent_steps = 8
max_tool_calls = 15
max_retries = 2
```

If limits are exceeded:

```text
STOP
 ↓
Safe fallback
```

---

# 54. P2 Cost Controls

Track:

```text
LLM calls
tokens
latency
estimated cost
agent retries
```

Avoid unbounded:

```text
agent → agent → agent → agent
```

---

# 55. P2 Observability

Track:

```text
conversation_id
agent_run_id
tool_call_id
agent_type
tool_name
latency
model
prompt_version
result
error
```

This produces an agent trace:

```text
User
 ↓
Orchestrator
 ↓
Buyer Agent
 ↓
search_products
 ↓
Offer Agent
 ↓
recommend_offer
 ↓
Checkout Agent
 ↓
get_quote
 ↓
policy_check
 ↓
payment
```

---

# 56. P2 Reliability

For normal AI tasks:

```text
AI failure
 ↓
Fallback
```

For financial operations:

```text
AI failure
 ↓
Stop ambiguous action
 ↓
Preserve state
 ↓
Require explicit retry / review
```

---

# 57. P2 Testing

## Agent tests

```text
[ ] correct agent selected
[ ] tools correctly called
[ ] invalid tool call rejected
[ ] agent loop stops
[ ] prompt injection handled
```

## Conversational checkout

```text
[ ] natural-language add-to-cart
[ ] cart state preserved
[ ] quote regenerated when required
[ ] payment boundary preserved
```

## Upsell

```text
[ ] compatible products
[ ] inventory
[ ] policy
[ ] duplicate recommendation prevention
```

## Campaigns

```text
[ ] discount limit
[ ] budget limit
[ ] simulation
[ ] merchant approval
```

## Risk

```text
[ ] normal transaction
[ ] high-value transaction
[ ] repeated attempts
[ ] policy violation
```

---

# 58. P2 Evaluation Dataset

Maintain:

```text
scenario_id
user_input
expected_intent
expected_constraints
expected_tool_sequence
expected_policy_result
```

Example:

```json
{
  "scenario_id": "buyer_001",
  "user_input": "Find ANC headphones under 5k.",
  "expected_constraints": {
    "max_budget": 500000,
    "required": ["ANC"]
  }
}
```

---

# 59. Regression Testing

Every major model/prompt change:

```text
New prompt/model
      ↓
Golden dataset
      ↓
Run evaluation
      ↓
Compare metrics
```

Reject changes that significantly degrade:

```text
constraint satisfaction
policy safety
tool correctness
```

---

# 60. P2 Deployment Architecture

```text
                         INTERNET
                            │
                    ┌───────┴────────┐
                    ▼                ▼
                React UI         Razorpay
                    │
                  HTTPS
                    │
                    ▼
              FastAPI Backend
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
   PostgreSQL      LLM       Background
                   │           Workers
                   ▼
              Agent Gateway
                   │
          ┌────────┼─────────┐
          ▼        ▼         ▼
       Buyer     Offer    Merchant
       Agent     Agent      Agent
          │        │         │
          └────────┼─────────┘
                   ▼
             Business Services
                   │
                   ▼
                Razorpay
```

---

# 61. Scaling Path

P2 MVP:

```text
FastAPI
PostgreSQL
BackgroundTasks
LLM
```

Later:

```text
FastAPI
PostgreSQL
Redis
Worker Queue
LLM Gateway
Event Broker
Observability
```

Only move to the second architecture when workload justifies it.

---

# 62. What NOT to Build

Unless everything else is already excellent:

```text
✕ Custom LLM training
✕ Reinforcement learning
✕ Fully autonomous financial agent
✕ Autonomous high-value purchases
✕ Autonomous refunds
✕ Kafka for the sake of architecture
✕ Kubernetes
✕ Complex vector infrastructure
✕ Hundreds of agents
✕ Unbounded agent loops
✕ Fully autonomous merchant changes
```

P2 is about **credible agentic commerce**, not maximum complexity.

---

# 63. P2 Implementation Order

## P2.1 — Agent Gateway

```text
Tool registry
 ↓
Permissions
 ↓
Validation
```

## P2.2 — Conversational Checkout

```text
Conversation
 ↓
Orchestrator
 ↓
Buyer tools
 ↓
Cart
 ↓
Quote
```

## P2.3 — Upsell / Cross-Sell

```text
Relationships
 ↓
Recommendation
 ↓
Offer
 ↓
Tracking
```

## P2.4 — Agent Evaluation

```text
Golden scenarios
 ↓
Evaluation
 ↓
Metrics
```

## P2.5 — Personalization

```text
Preferences
 ↓
Buyer context
 ↓
Recommendation improvement
```

## P2.6 — Campaigns

```text
Merchant objective
 ↓
AI strategy
 ↓
Simulation
 ↓
Approval
```

## P2.7 — Continuous Optimization

```text
Events
 ↓
Opportunities
 ↓
Recommendations
```

## P2.8 — Risk / Advanced Governance

```text
Risk
 ↓
Agent permissions
 ↓
Review
```

## P2.9 — Experiments

```text
Variants
 ↓
Simulation
 ↓
Real-world measurement
```

---

# 64. P2 Definition of Done

```text
[✓] Multiple agents operate through controlled tools
[✓] Conversational checkout works
[✓] Agent state is persistent
[✓] Upsell recommendations are relevant
[✓] Offers are measurable
[✓] Campaigns can be simulated
[✓] Merchant approves impactful changes
[✓] Agent actions are auditable
[✓] Agent performance is measurable
[✓] AI failures fail safely
[✓] Financial actions pass deterministic gates
```

---

# 65. Final P2 Architecture

```text
                         CUSTOMER
                            │
                            ▼
                 ┌────────────────────┐
                 │ Conversational UI  │
                 └──────────┬─────────┘
                            │
                            ▼
                 ┌────────────────────┐
                 │ AGENT ORCHESTRATOR │
                 └──────────┬─────────┘
                            │
          ┌─────────────────┼──────────────────┐
          ▼                 ▼                  ▼
     Buyer Agent       Offer Agent       Checkout Agent
          │                 │                  │
          └─────────────────┼──────────────────┘
                            ▼
                     AGENT GATEWAY
                            │
                    Permission + Tools
                            │
                            ▼
                  DETERMINISTIC SERVICES
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     Catalogue           Policy               Risk
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                          Quote
                            │
                            ▼
                      Authorization
                            │
                            ▼
                         Razorpay
                            │
                            ▼
                         Webhook
                            │
                            ▼
                          Events
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Analytics       Optimization       Evaluation
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    MERCHANT AI CENTER
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
      Campaigns          What-If           Insights
```

---

# 66. P2 North Star

The final system should feel like:

```text
Razorpay
   +
AI-native commerce infrastructure
```

not:

```text
A chatbot
   +
a payment page
```

The long-term loop is:

```text
UNDERSTAND
    ↓
RECOMMEND
    ↓
ACT
    ↓
MEASURE
    ↓
LEARN
    ↓
OPTIMIZE
    ↓
ACT AGAIN
```

with one permanent boundary:

```text
AI
 ↓
Proposal
 ↓
Tool Gateway
 ↓
Deterministic Validation
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Razorpay
```

**P2 is the layer that turns the product from an AI-enabled checkout into an extensible AI commerce platform.**


## September 4 Boundary Update
- No major changes. Analytics pipeline fully handles the high volume of friction signals generated by the full-catalogue evaluation.