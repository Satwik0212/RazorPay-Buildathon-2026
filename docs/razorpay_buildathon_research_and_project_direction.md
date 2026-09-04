# Razorpay AI Buildathon 2026 — Complete Research, Thinking & Project Direction

**Research snapshot:** 28 August 2026  
**Submission deadline:** 5 September 2026  
**Current track:** Track 01 — AI Growth & Agentic Commerce  
**Status:** Track selected; project architecture and implementation direction being finalized.

---

# 1. Why This Document Exists

This is the central research and thinking document for our Razorpay AI Buildathon project.

It records:

- what Razorpay is actually asking for
- what the Buildathon is really testing
- what Track 1 means
- what Razorpay already has in this space
- the problem/gap we are trying to address
- the directions we explored
- why we rejected some directions
- what we currently intend to build
- how we expect it to fit into Razorpay's environment
- what competitors/public builders are already attempting
- what we believe will make our submission stand out
- what we should demonstrate in the final video
- what we should NOT waste time building

This is intentionally different from `features.md`, `architecture.md`, `database.md`, and `tech.md`.

Those documents explain **what and how we build**.

This document explains:

> **Why are we building it, why should Razorpay care, and what are we trying to prove?**

---

# 2. First: What Razorpay Is Actually Doing With This Buildathon

The official Buildathon is not presented as a normal prize-based hackathon.

Razorpay describes it as:

> **"Build. Show. Get hired."**

It is a student-only program intended to discover and hire AI Builder Interns.

The official page explicitly says:

```text
No resume screening.
No long application.
Pick a track.
Build something real.
Show your work.
```

The submission is expected to include:

```text
Public GitHub repository
5-minute pitch video
Architecture
Working product
```

Razorpay's stated offer is an AI Builder Internship with:

```text
₹75,000/month
6 or 12 months
In-person, Bangalore
```

The important implication:

## This is partly a hiring evaluation disguised as a buildathon.

Razorpay is not only asking:

> "Is this idea cool?"

They are also effectively asking:

> "Would we want the person who built this to work on AI systems at Razorpay?"

That changes how we should approach the project.

---

# 3. What Razorpay Says It Wants

Across the official Buildathon description, the strongest signals are:

```text
Real AI
Real problem
Working product
Production-level thinking
Meaningful AI use
Reliability
Bounded actions
Explainability
Auditability
Failure handling
Business value
```

The wording differs by track, but the underlying evaluation philosophy is consistent.

The Buildathon is designed to surface builders who can move from:

```text
problem
  ↓
architecture
  ↓
implementation
  ↓
testing
  ↓
failure handling
  ↓
measurable outcome
```

rather than:

```text
LLM
  ↓
cool chatbot
  ↓
pretty UI
```

---

# 4. The Most Important Signal From Razorpay

For Track 1, Razorpay explicitly says:

> **Every money action should be explainable, bounded and gated. Show the audit trail and one failure handled gracefully.**

This single requirement is extremely important.

It tells us what Razorpay expects from an AI system operating around payments:

```text
AI
≠
unrestricted autonomous agent
```

Instead:

```text
AI
 ↓
reasoning
 ↓
proposal
 ↓
validation
 ↓
policy
 ↓
authorization
 ↓
execution
```

That is why our security architecture is intentionally strict.

---

# 5. The Five Tracks

Razorpay currently presents five tracks.

## Track 01 — AI Growth & Agentic Commerce

Goal:

```text
Grow merchant revenue
+
Make merchants sellable/transactable by AI buyers
```

Examples:

- Conversational in-app checkout
- Agent-readable catalog
- Upsell & cross-sell agent
- Campaign orchestrator

---

## Track 02 — AI Risk Manager

Goal:

```text
Prevent merchant losses
```

Examples:

- Chargeback evidence responder
- Return-risk scorer
- Fraud-spike detector
- Abuse-ring sentinel

Expected evidence:

```text
precision
recall
false-positive cost
held-out test set
```

---

## Track 03 — AI Revenue Recovery

Goal:

```text
Detect revenue at risk
→ diagnose
→ intervene
→ recover money
```

Examples:

- Payment degradation → root cause → recovery
- Checkout drop-off recovery
- Failed-subscription recovery
- Receivables chaser
- Mandate retry sequencer
- Hinglish voice recovery
- Promise-to-pay tracker

---

## Track 04 — AI Finance Controller

Goal:

```text
Automate a finance-operations loop
```

Examples:

- Multi-source reconciliation
- Settlement Q&A
- Cash forecasting
- Tax-line matching

Important requirement:

```text
50+ record batch
+
measured accuracy
+
exception list
```

---

## Track 05 — Open Track

Goal:

```text
Build what you believe should exist.
```

But the official page explicitly warns:

> Open does not mean easier.

The same expectations remain:

```text
real problem
working product
meaningful AI
value
reliability
depth
```

---

# 6. Why We Rejected Open Track

We initially considered Open Track.

The argument for it was:

```text
more freedom
more originality
less constraint
```

But that freedom also creates a problem.

We would have to simultaneously convince Razorpay:

```text
this problem matters
+
this belongs in Razorpay's ecosystem
+
this is better than an existing solution
+
AI is actually necessary
+
we can integrate it
```

Track 1 gives us a much stronger starting point.

Razorpay itself has already defined:

```text
merchant growth
+
AI buyers
+
agentic commerce
+
payment infrastructure
```

as an important strategic direction.

Therefore our job is not to invent the category.

Our job is to find a valuable missing layer inside it.

---

# 7. Why Track 1 Fits Our Current Direction

Track 1 is especially attractive because it allows us to combine:

```text
AI
+
software engineering
+
backend architecture
+
APIs
+
payments
+
agentic workflows
+
product thinking
```

It does not require us to train a new foundation model.

That matters.

The challenge is primarily about:

```text
using AI correctly
```

rather than:

```text
building a better LLM
```

This matches the kind of system we are capable of building:

```text
FastAPI
React
PostgreSQL
LLM/agents
structured outputs
tool calling
Razorpay test APIs
simulation
analytics
```

---

# 8. Understanding the Actual Razorpay Environment

Before choosing a project, we had a major conceptual problem:

> "How can we improve a merchant's growth if Razorpay isn't directly interacting with the end customer?"

This was the right question.

The answer is:

## Razorpay is the infrastructure layer.

A simplified relationship is:

```text
Customer
   ↓
Merchant's website/app
   ↓
Razorpay payment infrastructure
   ↓
Banks / UPI / Cards / Payment networks
```

Razorpay does not need to become the merchant's storefront to create value.

It already sits at an extremely important point in the transaction lifecycle.

That means an AI layer can potentially use:

```text
catalogue signals
cart signals
payment signals
transaction signals
merchant policies
customer intent
conversion signals
```

to create additional value.

---

# 9. The Key Strategic Insight

We initially thought:

> "If Razorpay doesn't own the user interface, how can it improve the merchant's sales?"

The more accurate framing is:

> **Razorpay can improve the systems surrounding the transaction.**

The merchant owns:

```text
brand
products
customers
catalogue
business rules
```

Razorpay provides:

```text
payment infrastructure
checkout infrastructure
transaction data
payment intelligence
merchant tooling
agentic payment infrastructure
```

Our project should therefore feel like:

```text
A new intelligent layer
inside Razorpay's existing merchant/payment ecosystem
```

not:

```text
A random e-commerce application using Razorpay.
```

---

# 10. Razorpay's Existing Agentic Direction

This is one of the most important pieces of external research.

Razorpay has already publicly positioned itself around **agentic payments**.

Its 2026 Sprint material describes the broader shift toward:

```text
AI-native commerce
agentic payments
AI-led shopping
payments inside conversations
```

Razorpay has also publicly described an Agentic Payments stack for:

```text
in-app commerce
LLM-based commerce
voice AI
```

The official Agentic Payments page describes the goal as enabling contextual checkout and allowing customers to complete purchases within conversational experiences.

Therefore:

## We should NOT build a generic "AI chatbot that can buy things."

Razorpay is already moving in that direction.

We need to build a meaningful layer around that infrastructure.

---

# 11. Razorpay's Existing AI Work Matters

Razorpay announced an Agent Studio in March 2026.

Its public description positions Agent Studio as a platform where agents can work alongside businesses for tasks such as:

```text
revenue recovery
payment management
financial operations
```

This means:

```text
"Razorpay + AI agents"
```

is not a new idea.

That makes generic agent demos weaker.

Our project has to answer:

> **What useful capability are we adding that fits naturally into this direction?**

---

# 12. The Strategic Timing

Razorpay itself cites the rise of:

```text
NPCI UAP
ACP
AP2
x402
```

as part of the reason agentic commerce is becoming important.

At the same time, NPCI has been actively exploring AI and conversational payments.

NPCI's UPI ecosystem already includes conversational initiatives such as:

```text
UPI Help
Hello! UPI
```

and its 2026 FiMI work shows that payment-native AI is becoming a serious infrastructure problem rather than just a chatbot experiment.

Therefore:

```text
AI
+
Payments
+
Commerce
```

is not hype from our side.

It is a real industry direction.

---

# 13. What "AI Buyer" Actually Means

The important shift is:

Traditional commerce:

```text
Human
 ↓
Website
 ↓
Search
 ↓
Product
 ↓
Cart
 ↓
Checkout
 ↓
Payment
```

Agentic commerce:

```text
Human
 ↓
AI Agent
 ↓
Intent
 ↓
Product discovery
 ↓
Decision
 ↓
Purchase
 ↓
Payment
```

The AI buyer becomes a new type of customer interface.

That creates a new problem:

> How does a merchant make its products understandable, selectable and transactable by AI agents?

This is one of the core reasons Track 1 exists.

---

# 14. Directions We Explored

We did not immediately choose a project.

We explored the problem from several angles.

---

# 15. Direction A — Conversational In-App Checkout

Razorpay's suggested direction:

```text
User speaks naturally
 ↓
AI understands intent
 ↓
Products selected
 ↓
Checkout
 ↓
Payment
```

Example:

```text
"I need a laptop under ₹60k for programming."
```

Agent:

```text
understands constraints
↓
searches catalogue
↓
compares products
↓
recommends
↓
adds to cart
↓
checkout
```

### Strength

Very aligned with Razorpay's agentic-commerce strategy.

### Problem

A basic version is not sufficiently differentiated.

Razorpay itself is already publicly building toward conversational/in-app payments.

Therefore:

```text
Conversational checkout alone
```

is not enough.

---

# 16. Direction B — Agent-Readable Catalog

Problem:

Traditional product catalogue:

```text
name
price
description
image
```

AI agents need:

```text
structured attributes
constraints
compatibility
availability
delivery
policy
relationships
merchant rules
```

Potential system:

```text
Merchant catalogue
       ↓
AI-readable representation
       ↓
AI buyer
       ↓
Product discovery
```

### Strength

This solves a real emerging problem.

### Problem

If implemented only as:

```text
"convert product descriptions to JSON"
```

it becomes too shallow.

The interesting part is not merely:

```text
make catalogue readable
```

but:

```text
make catalogue reliably transactable by AI
```

---

# 17. Direction C — Upsell & Cross-Sell Agent

Basic idea:

```text
Customer buys laptop
 ↓
AI recommends mouse/bag/warranty
```

This directly affects:

```text
AOV
cross-sell rate
merchant revenue
```

### Strength

Easy to explain.

### Problem

A basic recommendation engine is extremely common.

If the implementation is:

```text
product
 ↓
LLM
 ↓
"you may also like"
```

then it is not enough.

The system needs:

```text
context
+
inventory
+
price sensitivity
+
merchant objective
+
customer intent
+
measured outcome
```

---

# 18. Direction D — Campaign Orchestrator

Merchant says:

```text
"Increase headphone sales this weekend."
```

AI:

```text
analyses catalogue
+
inventory
+
historical performance
+
customer segments
+
offers
```

then proposes:

```text
campaign
+
target products
+
offer strategy
+
expected impact
```

### Strength

Very strong merchant-side product thinking.

### Problem

Campaign automation can become too broad very quickly.

If we attempt:

```text
full marketing automation
```

we risk building an enormous system.

---

# 19. Direction E — Revenue Recovery

This was another major direction.

Basic idea:

```text
Payment fails
 ↓
Diagnose
 ↓
Choose recovery action
 ↓
Recover payment
```

At first this looked attractive.

But we identified an important weakness.

A simplistic system becomes:

```text
payment failed
 ↓
try UPI
```

or:

```text
timeout
 ↓
retry
```

That is not sufficiently novel.

Users already know they can:

```text
retry
change payment method
try again
```

Therefore:

> **A generic payment-failure assistant is not enough.**

---

# 20. The Automation Question

We then asked:

> What if the AI automatically retries or changes the payment method?

This is where safety becomes a major problem.

You cannot casually build:

```text
AI
 ↓
take control of payment
 ↓
change payment method
 ↓
retry money movement
```

without:

```text
authorization
policy
risk
idempotency
limits
audit
```

Therefore, autonomous payment execution is possible only inside strict boundaries.

This insight strongly influenced our architecture.

---

# 21. The Biggest Lesson From Exploring Recovery

The lesson was not:

> "Revenue recovery is bad."

It was:

> **Don't build an AI wrapper around an obvious manual action.**

A useful AI system should make a decision that was previously:

```text
expensive
slow
complex
data-heavy
hard to personalize
```

rather than simply:

```text
clicking Retry automatically.
```

---

# 22. What We Believe Razorpay Is Actually Testing

After studying the Buildathon wording and Razorpay's existing AI direction, our current interpretation is that Razorpay is testing four things simultaneously:

## 1. Product taste

Can you identify:

```text
a real problem
```

rather than:

```text
a cool technology
```

?

## 2. AI judgment

Do you know:

```text
where AI is useful
```

and:

```text
where deterministic software is better
```

?

## 3. Engineering judgment

Can you build:

```text
reliable APIs
database
state management
failure recovery
security
```

?

## 4. Ownership

Can you take:

```text
idea
→ architecture
→ implementation
→ testing
→ demo
```

without leaving the hard parts hidden?

---

# 23. Our Biggest Change in Thinking

Initially we were thinking:

```text
"What AI feature should we make?"
```

We have moved toward:

```text
"What new capability can Razorpay add to its ecosystem,
using AI where it actually creates leverage?"
```

This is a much better question.

---

# 24. Our Current Project Thesis

Our current working thesis is:

> **Build an AI-native commerce layer that lets merchants understand how AI buyers behave, optimize their catalogue/offers for those buyers, and eventually allow those optimized experiences to flow into secure transaction execution through Razorpay.**

In simplified form:

```text
Merchant
   ↓
Catalogue + business data
   ↓
AI Buyer Simulation
   ↓
Understand buyer behaviour
   ↓
Merchant Optimization
   ↓
Better catalogue / offers / strategy
   ↓
AI Buyer
   ↓
Commerce
   ↓
Razorpay Payment
```

---

# 25. The Core Loop

The product should ultimately create this loop:

```text
UNDERSTAND
    ↓
SIMULATE
    ↓
IDENTIFY PROBLEMS
    ↓
OPTIMIZE
    ↓
TEST
    ↓
MEASURE
    ↓
IMPROVE
```

The merchant should not merely receive:

```text
"AI says this is better."
```

They should receive:

```text
"This buyer segment behaves like this."

"This product loses this type of buyer."

"Changing X may improve Y."

"Simulation predicts Z."

"After applying the change, observed results were..."
```

That is a much stronger product story.

---

# 26. AI Buyer Simulation

This is one of the central differentiators in our current direction.

Instead of only asking:

```text
"What product should this customer buy?"
```

we ask:

> **"How would different AI buyers behave when interacting with this merchant?"**

Examples:

```text
Budget Buyer
Speed-Focused Buyer
Quality-Focused Buyer
Compatibility-Focused Buyer
Deal-Seeking Buyer
Brand-Loyal Buyer
```

Each simulated buyer can have:

```text
constraints
preferences
budget
urgency
decision criteria
risk tolerance
```

---

# 27. Why Simulation Is Interesting

Traditional merchant analytics tells:

```text
what happened
```

AI buyer simulation can explore:

```text
what might happen
```

Example:

```text
Merchant has 100 products.

Simulation:
1,000 AI buyer scenarios.

Result:
- 31% fail to find a suitable product
- 18% abandon due to unclear compatibility
- 12% reject because delivery information is insufficient
- 9% select a lower-margin alternative
```

This gives the merchant something actionable.

---

# 28. Important Warning About Simulation

Simulation is NOT real-world truth.

Therefore we must never present:

```text
"Revenue will increase by 23%."
```

as a fact.

Instead:

```text
"Under the simulated buyer distribution,
Variant B produced 18% higher simulated conversion."
```

Then clearly separate:

```text
SIMULATED
```

from:

```text
OBSERVED
```

This distinction is essential for credibility.

---

# 29. Merchant Optimization

The next layer is:

```text
Simulation
 ↓
Identify friction
 ↓
Generate optimization
```

Potential optimization targets:

```text
product metadata
catalogue structure
recommendation ranking
cross-sell
upsell
offer
bundle
campaign
buyer-facing explanation
```

The AI should generate:

```text
recommendation
reason
expected impact
confidence
risk
```

not silently change production state.

---

# 30. The "Bloat" Decision

We explicitly discussed whether to include every possible feature.

Current decision:

> **Do not start with bloat.**

Core system first:

```text
AI Buyer Simulation
+
Merchant Optimization
```

Only after this is stable should we consider:

```text
conversational checkout
upsell
cross-sell
campaigns
additional agent tools
```

The rule is:

```text
Core product first.
Extra features last.
```

---

# 31. Why This Is Important

A common hackathon failure mode is:

```text
15 features
0 deep features
```

We want:

```text
2-4 connected capabilities
+
deep implementation
+
real metrics
+
security
+
failure handling
```

A reviewer should understand the entire product in under one minute.

---

# 32. What We Want Razorpay to See

The demo should communicate:

> "This isn't another chatbot."

Instead:

```text
This is a merchant intelligence + AI-commerce system.
```

It should demonstrate:

```text
Merchant enters catalogue
        ↓
AI buyer profiles are generated
        ↓
Buyers interact with merchant system
        ↓
Simulation produces measurable friction
        ↓
AI identifies optimization opportunities
        ↓
Merchant accepts an optimization
        ↓
System simulates again
        ↓
Results improve
```

Then:

```text
Razorpay payment layer
```

shows how the optimized commerce flow eventually reaches transaction execution.

---

# 33. Why Razorpay Should Care

A strong pitch must answer this.

Potential value:

## Merchant value

```text
higher conversion
higher AOV
better product discovery
better AI compatibility
better campaign decisions
less manual optimization
```

## Customer/AI buyer value

```text
faster discovery
better recommendations
less friction
clearer product information
more reliable checkout
```

## Razorpay value

```text
more successful transactions
more merchant GMV
stronger agentic-commerce infrastructure
more valuable merchant tooling
greater relevance in AI-led commerce
```

The strongest connection is:

> **If AI becomes a major buyer interface, Razorpay can help merchants become optimized for that interface while remaining the trusted transaction layer underneath.**

---

# 34. Razorpay Integration Philosophy

We should never pitch:

```text
"Replace Razorpay."
```

We should pitch:

```text
"Extend Razorpay."
```

Architecture:

```text
Merchant
   ↓
Our AI Commerce Layer
   ↓
Razorpay APIs / test mode
   ↓
Payment Infrastructure
```

This makes the project feel like:

```text
a possible Razorpay product
```

rather than:

```text
an external startup using Razorpay.
```

---

# 35. Razorpay APIs and Test Mode

The project should be designed around Razorpay's test-mode environment.

The exact API calls should be implemented against the current official documentation rather than guessed.

Conceptually:

```text
Our Backend
   ↓
Razorpay SDK / REST API
   ↓
Orders
   ↓
Checkout
   ↓
Payments
   ↓
Webhooks
```

The important point is:

> We do not need to recreate a payment gateway.

We need to demonstrate how our AI layer interacts with the payment infrastructure.

---

# 36. The Security Model

The architecture has one permanent rule:

```text
AI ≠ Financial Authority
```

AI can:

```text
reason
recommend
simulate
rank
explain
request an action
```

Deterministic services control:

```text
price
quote
policy
inventory
authorization
payment state
```

Razorpay handles:

```text
payment execution
```

This separation is one of the strongest technical aspects of the project.

---

# 37. Trust Architecture

Our final security chain is:

```text
AI
 ↓
Tool Gateway
 ↓
Pydantic Validation
 ↓
Business Validation
 ↓
Quote
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Razorpay
 ↓
Webhook Verification
 ↓
Database State
 ↓
Audit Trail
```

The more autonomous the AI becomes:

```text
more AI autonomy
        ↓
more governance
```

not:

```text
more AI autonomy
        ↓
less control
```

---

# 38. Why This Matters Specifically to Razorpay

A payment company cannot accept:

```text
LLM hallucinated amount
LLM invented payment status
LLM arbitrary database mutation
LLM uncontrolled retry
LLM direct payment execution
```

Therefore the architecture itself becomes part of the product.

A reviewer should be able to see:

```text
Here is what AI decides.

Here is what AI cannot decide.

Here is where policy takes over.

Here is where payment authority begins.

Here is the audit trail.
```

---

# 39. What We Learned From Public Competition

Public competition data is still limited because the Buildathon is ongoing.

This is important:

> **We do not currently have evidence supporting a claim like "80,000 participants" or "30,000 people are building Track 1."**

Community posts show uncertainty about participation and track competition, but they do not provide reliable counts.

Therefore we should treat:

```text
"there will be huge competition"
```

as a reasonable strategic assumption,

but not:

```text
"80,000 people are competing"
```

as a fact.

---

# 40. Public Competition We Can Actually Verify

One public GitHub repository is particularly relevant:

```text
Revenue Resilience AI
```

It targets the Razorpay Buildathon and focuses on safe revenue recovery.

Its architecture is notably serious.

It uses:

```text
LLM
 ↓
typed diagnosis
 ↓
deterministic policy engine
 ↓
idempotent state store
 ↓
executor
```

The repository explicitly removes execution authority from the LLM.

This is very close to the safety philosophy we independently arrived at.

---

# 41. What That Competition Teaches Us

The public repository demonstrates that competitors are already thinking beyond:

```text
"LLM + payment API"
```

They are thinking about:

```text
deterministic policy
idempotency
failure injection
audit trails
economic thresholds
LLM trust boundaries
```

Therefore our engineering standard needs to be high.

---

# 42. Another Important Competition Signal

The public project includes explicit failure-injection scenarios:

```text
concurrent webhooks
stale reservations
duplicate executor
```

This is exactly the type of detail that can differentiate a serious engineering submission from a prototype.

Therefore our own project should also demonstrate at least one meaningful failure.

---

# 43. What Public Community Discussion Tells Us

Reddit discussion around the Buildathon shows that many participants are still asking:

```text
Which track?
What should we build?
How much competition?
How should the video be recorded?
Is the repository compulsory?
```

This suggests the public competition is not yet mature enough for us to reverse-engineer a dominant winning pattern.

That is good.

It means:

```text
we should not chase a perceived trend
```

based on weak evidence.

---

# 44. Current Competitive Landscape

Based on what can currently be verified publicly:

| Category | Evidence |
|---|---|
| Revenue recovery | At least one serious public GitHub project |
| Agentic commerce | Strongly implied by many community discussions |
| Conversational payments | Strong Razorpay ecosystem direction |
| Agent-readable catalogue | Official Buildathon direction |
| Upsell/cross-sell | Official Buildathon direction |
| Campaign orchestration | Official Buildathon direction |
| Exact number of Track 1 competitors | Unknown |
| Exact number of total submissions | Unknown |
| Dominant winning architecture | Unknown |

This is why we should optimize for:

```text
execution quality
+
product clarity
+
engineering depth
```

rather than guessed competitor counts.

---

# 45. What We Should NOT Copy From Competitors

Even if public repositories are available, copying the surface idea is dangerous.

We can learn from:

```text
architecture
failure handling
schemas
testing strategy
API patterns
security patterns
```

But our product thesis must remain our own.

The goal is:

```text
reuse engineering patterns
```

not:

```text
clone the project.
```

---

# 46. Our Competitive Advantage

Our current opportunity is to combine:

```text
AI Buyer Simulation
+
Merchant Optimization
+
Razorpay transaction layer
+
strong safety architecture
+
measurable simulation
+
production-oriented backend
```

Most simplistic projects will likely focus on one:

```text
chatbot
recommendation
checkout
campaign
```

Our aim is to connect them into one loop.

---

# 47. The Product Loop We Want to Show

```text
MERCHANT
   │
   ▼
CATALOGUE
   │
   ▼
AI BUYER SIMULATION
   │
   ▼
BUYER BEHAVIOUR
   │
   ▼
FRICTION / OPPORTUNITY
   │
   ▼
AI OPTIMIZATION
   │
   ▼
MERCHANT APPROVAL
   │
   ▼
NEW VERSION
   │
   ▼
SIMULATION
   │
   ▼
MEASURED CHANGE
```

Then:

```text
REAL BUYER
   ↓
COMMERCE
   ↓
RAZORPAY
   ↓
PAYMENT
```

---

# 48. The Product Should Have Two Sides

This is important.

## Merchant side

```text
Dashboard
 ↓
Catalogue
 ↓
Buyer Simulation
 ↓
Insights
 ↓
Optimization
 ↓
Experiments
 ↓
Results
```

## Buyer side

```text
AI Buyer
 ↓
Intent
 ↓
Catalogue discovery
 ↓
Recommendation
 ↓
Cart
 ↓
Checkout
 ↓
Payment
```

The merchant side learns from the buyer side.

That is the loop.

---

# 49. P0 / P1 / P2 Thinking

Our implementation is deliberately staged.

## P0 — Core Foundation

Focus on:

```text
authentication
merchant
catalogue
products
inventory
cart
quote
payment flow
Razorpay integration
webhooks
security
audit
```

Without this:

```text
AI features are just demos.
```

---

## P1 — Core Intelligence

Focus on:

```text
AI Buyer Simulation
buyer personas
scenario generation
simulation engine
merchant analytics
friction detection
optimization recommendations
what-if comparison
```

This is the heart of the project.

---

## P2 — Expansion

Only after P0 + P1 are stable:

```text
conversational checkout
upsell/cross-sell
campaign orchestration
personalized buyer memory
multi-agent orchestration
experimentation
advanced risk
continuous optimization
```

P2 is optional.

---

# 50. Why We Are Keeping P2 Last

Because the strongest submission is not:

```text
"Look! We have 17 AI agents."
```

It is:

```text
"Here is the problem.
Here is the system.
Here is the measurable result.
Here is how it fails safely.
Here is how it integrates with Razorpay."
```

Depth beats feature count.

---

# 51. What "Production-Level" Means For Us

We should not interpret production-level as:

```text
Kubernetes
Kafka
microservices everywhere
100 endpoints
massive infrastructure
```

Instead:

```text
clear boundaries
validated inputs
correct state
safe transactions
idempotency
error handling
observability
tests
security
reproducibility
```

A well-designed FastAPI monolith can be more production-like than a badly designed distributed system.

---

# 52. What We Should Measure

A serious project needs metrics.

For simulation:

```text
buyers simulated
successful product matches
failed matches
constraint satisfaction
abandonment rate
decision time
```

For optimization:

```text
baseline score
optimized score
simulated conversion
simulated AOV
catalogue completeness
buyer constraint satisfaction
```

For AI:

```text
tool-call accuracy
constraint satisfaction
invalid action rate
hallucination/error rate
latency
cost
```

For payment:

```text
successful transactions
failed transactions
duplicate attempts
webhook processing
reconciliation
```

---

# 53. The Baseline Is Important

Never show only:

```text
AI result = 82%
```

Show:

```text
Baseline = 61%
AI optimized = 82%
Improvement = +21 percentage points
```

Even better:

```text
AI optimized
vs
simple heuristic baseline
```

This proves that AI is adding value.

---

# 54. Simulation Evaluation

The simulation engine should have controlled scenarios.

Example:

```text
Scenario:
Buyer wants ANC headphones
Budget ≤ ₹5,000
Delivery ≤ 2 days
Brand preference = none
```

Expected behaviour:

```text
find valid products
respect budget
respect ANC
respect delivery
```

Then evaluate:

```text
Did the AI satisfy all constraints?
```

This makes the simulation measurable rather than subjective.

---

# 55. Optimization Evaluation

Example:

```text
BEFORE

Buyer success:
62%

After catalogue optimization:

Buyer success:
78%
```

Then show:

```text
+16 percentage points
```

This is much stronger than:

```text
"AI improved the catalogue."
```

---

# 56. Failure We Should Demonstrate

Razorpay explicitly wants a failure handled gracefully.

Our demo should include something meaningful.

Possible example:

```text
Payment/webhook arrives twice
```

System:

```text
Webhook #1
 ↓
processed

Webhook #2
 ↓
duplicate detected
 ↓
no duplicate transaction
 ↓
audit logged
```

Or:

```text
AI recommends invalid action
 ↓
Pydantic/business validation
 ↓
blocked
 ↓
safe fallback
```

Or:

```text
Quote expires
 ↓
payment blocked
 ↓
fresh quote generated
```

This is much more convincing than intentionally crashing the UI.

---

# 57. What the Final Pitch Must Prove

The 5-minute video should answer:

## 1. Problem

```text
What is broken?
```

## 2. Why Razorpay

```text
Why does this belong inside Razorpay?
```

## 3. Solution

```text
What did we build?
```

## 4. AI

```text
Why is AI necessary?
```

## 5. Architecture

```text
How does it work?
```

## 6. Safety

```text
How can Razorpay trust it?
```

## 7. Evidence

```text
What improved?
```

## 8. Failure

```text
What broke and how did we handle it?
```

## 9. Future

```text
What could this become inside Razorpay?
```

---

# 58. The Pitch Should NOT Sound Like This

Avoid:

```text
"We use LangChain."
"We use Gemini."
"We use FastAPI."
"We have 7 agents."
"We use RAG."
"We use PostgreSQL."
```

Those are implementation details.

They are not the product.

---

# 59. The Pitch Should Sound Like This

Something closer to:

```text
"AI agents are becoming buyers.

Today, merchants optimize for human shoppers,
but an AI buyer evaluates products differently.

We built a system that lets a merchant simulate
AI buyers, discover where those buyers fail,
and optimize the catalogue and commerce experience
before those failures happen in production.

The same system is designed to flow into Razorpay's
agentic payment infrastructure, with every financial
action bounded by deterministic policy and verified
payment state."
```

That is a product thesis.

---

# 60. What We Want the Reviewer to Think

Ideal reaction:

```text
"Interesting problem."

"That actually fits Razorpay."

"They understand agentic commerce."

"They understand payments."

"They didn't let the LLM control money."

"They measured the result."

"They tested failure."

"They built the backend properly."

"This could become a real product."
```

That is the target.

---

# 61. What We Should Avoid

## Avoid generic chatbot UI

```text
User → Chatbot → answer
```

Too easy.

## Avoid AI wrapper around CRUD

```text
AI → database CRUD
```

Not enough.

## Avoid fake analytics

```text
random numbers
```

Use generated/synthetic data honestly and label it.

## Avoid fake revenue claims

Never say:

```text
"we increased revenue by 30%"
```

unless we actually measured it.

## Avoid uncontrolled autonomous payment

Too risky.

## Avoid feature bloat

More buttons do not equal more product.

---

# 62. What We Should Build Deeply

The highest-priority components are:

```text
1. Merchant catalogue
2. AI Buyer Simulator
3. Buyer personas/scenarios
4. Simulation engine
5. Friction detection
6. Optimization engine
7. Merchant dashboard
8. Razorpay test-mode payment flow
9. Security / policy layer
10. Audit trail
11. Failure demonstration
12. Evaluation metrics
```

Everything else is secondary.

---

# 63. The Engineering Philosophy

Our architecture follows:

```text
Probabilistic
        ↓
AI reasoning
        ↓
Structured output
        ↓
Deterministic
        ↓
Validation
        ↓
Policy
        ↓
Execution
```

This is especially important because another public Buildathon project has already demonstrated a similar principle in the revenue-recovery space: its LLM only produces a typed diagnosis while a deterministic policy engine decides whether an action is permitted.

That means this is becoming a recognizable pattern for serious AI + payments engineering.

Our implementation should therefore go beyond merely copying the pattern and apply it naturally to AI commerce.

---

# 64. Our Database Philosophy

The database is not just storage.

It must allow us to answer:

> "Exactly what happened?"

For every transaction:

```text
customer
 ↓
intent
 ↓
cart
 ↓
quote
 ↓
authorization
 ↓
order
 ↓
Razorpay order
 ↓
payment
 ↓
webhook
 ↓
audit
```

For every AI decision:

```text
conversation
 ↓
agent run
 ↓
prompt version
 ↓
tool call
 ↓
input
 ↓
output
 ↓
policy
 ↓
action
```

This is important for debugging and trust.

---

# 65. Our Security Philosophy

The strongest rule:

```text
AI ≠ Financial Authority
```

The system must enforce:

```text
No AI-generated amount is authoritative.

No frontend amount is authoritative.

No browser success message proves payment.

No unverified webhook changes payment state.

No duplicate webhook causes duplicate execution.

No agent gets unrestricted tools.

No payment action happens without policy/authorization.
```

This is why `safety_regulations.md` exists.

---

# 66. What "Razorpay-Native" Means For Us

A project is not Razorpay-native merely because it has:

```text
Razorpay logo
+
Razorpay Checkout
```

A more convincing Razorpay-native system understands:

```text
merchant
+
catalogue
+
checkout
+
payment
+
transaction
+
agentic commerce
+
revenue
+
risk
+
audit
```

and places the new capability inside that ecosystem.

---

# 67. Integration Story

The future architecture should look like:

```text
                    RAZORPAY ECOSYSTEM

Merchant
   │
   ▼
AI Commerce Intelligence
   │
   ├── Buyer Simulation
   ├── Catalogue Intelligence
   ├── Optimization
   ├── Offers
   └── Campaigns
   │
   ▼
Agentic Commerce
   │
   ▼
Razorpay Checkout / Payments
   │
   ▼
Transaction
   │
   ▼
Events
   │
   └──────────────┐
                  ▼
             Optimization
```

This creates a feedback loop.

---

# 68. The Feedback Loop Is the Real Product

The strongest version is not:

```text
AI recommends something.
```

It is:

```text
AI observes
 ↓
AI simulates
 ↓
AI recommends
 ↓
Merchant approves
 ↓
System executes
 ↓
Outcome measured
 ↓
System learns
 ↓
Next recommendation
```

That is where the product becomes genuinely interesting.

---

# 69. What We Think Razorpay Wants From the Candidate

Our current interpretation:

### Product sense

```text
Can you identify valuable problems?
```

### AI sense

```text
Can you use AI without abusing it?
```

### Engineering sense

```text
Can you make it reliable?
```

### Fintech sense

```text
Do you understand that money systems need stronger guarantees?
```

### Ownership

```text
Can you take the thing from idea to working system?
```

---

# 70. What We Want to Prove About Ourselves

The project is also a demonstration of engineering maturity.

We want the repository to show:

```text
daily thinking
research
architecture
database design
security decisions
technical decisions
implementation
tests
failures
fixes
metrics
```

That is why we are maintaining:

```text
Daily logs
features.md
architecture.md
p0_tech.md
p1_tech.md
p2_tech.md
safety_regulations.md
database.md
```

The repository itself becomes evidence of how we build.

---

# 71. Our Daily Development Log Strategy

Every day should answer:

```text
What did I do?
What did I learn?
What changed?
What failed?
What decision did I make?
What is next?
```

This helps with:

```text
final pitch
technical interview
architecture explanation
failure story
```

---

# 72. Failure Is Not Something to Hide

One of the strongest signals Razorpay asks for is failure recovery.

Therefore we should not pretend:

```text
everything worked perfectly.
```

A stronger story is:

```text
We initially allowed X.

We discovered Y failure.

We realized Z risk.

We changed the architecture.

Now the system guarantees A.
```

This demonstrates engineering judgment.

---

# 73. Our Expected Failure Story

We should intentionally document at least one architectural correction.

Potential examples:

```text
initial AI action was too autonomous
→ introduced policy gateway

initial payment state was client-driven
→ moved authority server-side

duplicate webhook caused repeated processing
→ introduced event idempotency

simulation produced optimistic results
→ introduced baseline + held-out scenarios

recommendation ignored inventory
→ added deterministic inventory validation
```

The exact story should come from something that genuinely happens during development.

Never fabricate a failure.

---

# 74. Competition Strategy

We should NOT try to win by:

```text
having the most features
```

or:

```text
having the fanciest UI
```

or:

```text
having the most agents
```

We should try to win through:

```text
problem quality
+
product coherence
+
engineering depth
+
AI judgment
+
measurable evidence
+
trustworthiness
```

---

# 75. Our Current Competitive Position

At this point, our strongest possible differentiation is:

```text
AI Buyer Simulation
+
Merchant Optimization
+
Razorpay integration
+
strong transaction safety
+
measurable evaluation
```

This is not guaranteed to be unique.

But it is a coherent product thesis.

Our job now is to execute it better than the average submission.

---

# 76. What We Should Keep From Public Repositories

Public repositories can save implementation time.

We should look for:

```text
authentication patterns
FastAPI structure
React components
agent orchestration
Pydantic models
Razorpay integration
webhook handlers
testing
idempotency
audit logging
simulation infrastructure
```

But we should not blindly import:

```text
architecture
business logic
product concept
```

if they don't fit our system.

---

# 77. The "Borrow Engineering, Not Identity" Rule

For every repository we inspect:

```text
Can we reuse this?
```

Ask:

```text
Does it solve a generic engineering problem?
```

If yes:

```text
reuse/adapt pattern
```

If it defines:

```text
their product's core identity
```

then:

```text
learn from it
don't clone it
```

---

# 78. Why the Three-Day / Limited-Time Constraint Matters

We have limited implementation time.

Therefore our priorities should be:

```text
P0 foundation
 ↓
P1 core intelligence
 ↓
testing
 ↓
demo
 ↓
pitch
 ↓
only then P2
```

Not:

```text
P0
 ↓
P2
 ↓
random UI
 ↓
another agent
 ↓
campaign
 ↓
panic
```

---

# 79. The Final Product in One Sentence

Our current working one-liner:

> **An AI commerce intelligence layer for Razorpay that simulates AI buyers, identifies where merchants lose AI-driven purchases, and recommends measurable catalogue and commerce optimizations before those failures reach real transactions.**

This is a working thesis, not the final marketing copy.

---

# 80. Three-Line Core Ideation

```text
AI buyers are becoming a new customer interface.

Merchants need to understand how those buyers discover,
evaluate and reject products.

We simulate those buyers, identify friction,
and optimize the merchant's commerce experience
while Razorpay remains the trusted transaction layer.
```

---

# 81. Final Architecture Philosophy

```text
                    MERCHANT
                       │
                       ▼
                  CATALOGUE
                       │
                       ▼
              AI BUYER SIMULATOR
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Buyer Behaviour       Friction
             │                   │
             └─────────┬─────────┘
                       ▼
               OPTIMIZATION AI
                       │
                       ▼
                MERCHANT REVIEW
                       │
                       ▼
                 EXPERIMENT
                       │
                       ▼
                  MEASURE
                       │
                       ▼
                 REAL COMMERCE
                       │
                       ▼
                  RAZORPAY
                       │
                       ▼
                  PAYMENT
                       │
                       ▼
                   EVENTS
                       │
                       └──────────→ OPTIMIZATION
```

---

# 82. Final Security Architecture

```text
AI
 ↓
Structured Output
 ↓
Pydantic
 ↓
Business Validation
 ↓
Policy
 ↓
Risk
 ↓
Authorization
 ↓
Payment Service
 ↓
Razorpay
 ↓
Webhook
 ↓
Signature Verification
 ↓
State Validation
 ↓
Audit
```

---

# 83. Final Product Priorities

## Tier 0 — Must Work

```text
✓ Merchant
✓ Catalogue
✓ Cart
✓ Quote
✓ Razorpay test payment
✓ Webhook
✓ Database
✓ Authentication
✓ Security
```

## Tier 1 — Must Impress

```text
✓ AI Buyer Simulation
✓ Buyer personas
✓ Scenario generation
✓ Constraint evaluation
✓ Friction detection
✓ Merchant optimization
✓ Before/after metrics
✓ What-if analysis
```

## Tier 2 — Nice to Have

```text
Conversational checkout
Upsell
Cross-sell
Campaigns
Buyer memory
Experiments
Multi-agent orchestration
```

---

# 84. Final Definition of Success

We should consider the project successful if a reviewer can see this sequence:

```text
1. Merchant uploads/creates catalogue.

2. System creates realistic AI buyer scenarios.

3. AI buyers interact with the commerce experience.

4. The system measures where buyers succeed/fail.

5. AI identifies why.

6. AI proposes an optimization.

7. Merchant can inspect and approve it.

8. System runs the scenario again.

9. Measurable improvement is shown.

10. A real test-mode transaction flows through Razorpay.

11. A failure/duplicate/invalid action is handled safely.

12. The architecture explains exactly why the system can be trusted.
```

If we can do this cleanly, the project has a strong story.

---

# 85. What We Should Be Able to Say in the Final Interview

If a Razorpay engineer asks:

### "Why did you choose this problem?"

Answer:

```text
Because agentic commerce changes the customer interface.

Merchants already optimize for human browsing,
but AI buyers will evaluate products through structured
constraints, preferences and goals.

We wanted to give merchants a way to understand
and optimize for that new buyer.
```

### "Why AI?"

```text
Because buyer intent and product suitability are
semantic and highly variable.

But we keep money movement deterministic.
```

### "Why Razorpay?"

```text
Because Razorpay sits directly in the merchant
commerce and payment infrastructure and is already
moving toward agentic payments.
```

### "Why should we trust it?"

```text
The AI never has direct financial authority.

Every financial action passes through validation,
policy, authorization and verified payment state.
```

### "What happens when AI is wrong?"

```text
The system rejects invalid structured output,
falls back safely, records the event,
and does not allow AI to override financial truth.
```

---

# 86. The Most Important Strategic Decision

We are NOT building:

```text
an AI shopping chatbot.
```

We are NOT building:

```text
a generic recommendation engine.
```

We are NOT building:

```text
an automatic payment retry bot.
```

We are NOT building:

```text
a fake autonomous payment agent.
```

We are trying to build:

> **A merchant-side AI commerce intelligence system that helps merchants become better prepared for AI-driven purchasing.**

The transaction layer is where Razorpay naturally enters.

---

# 87. Current North Star

```text
Today's merchant:

Human buyer
    ↓
Catalogue
    ↓
Checkout
    ↓
Payment


Our vision:

AI buyer
    ↓
Intent
    ↓
Catalogue understanding
    ↓
Decision
    ↓
Optimized commerce
    ↓
Secure transaction
    ↓
Razorpay
```

And on the merchant side:

```text
Observe
 ↓
Simulate
 ↓
Optimize
 ↓
Experiment
 ↓
Measure
 ↓
Repeat
```

---

# 88. Final Mental Model

The project should always be thought of as three connected layers.

## Layer 1 — Intelligence

```text
AI Buyer
AI Simulation
AI Optimization
```

## Layer 2 — Commerce

```text
Catalogue
Cart
Quote
Offers
Campaigns
```

## Layer 3 — Payments

```text
Authorization
Razorpay Order
Payment
Webhook
Audit
```

And the boundary between them is:

```text
AI can recommend.

Commerce services validate.

Payment services execute.

Razorpay confirms.
```

---

# 89. Final Conclusion

The Buildathon is not asking us to make the most impressive-looking AI demo.

It is asking us to demonstrate that we can build something that belongs in a real fintech/commerce environment.

The official Track 1 framing gives us a strong direction:

```text
merchant growth
+
AI buyers
+
agentic commerce
```

Razorpay's own product direction confirms that agentic payments are becoming strategically important.

That creates an opportunity, but it also raises the bar.

A generic conversational checkout is too close to what Razorpay is already publicly pursuing.

A generic recommendation engine is too shallow.

A generic payment-retry assistant is too obvious and too risky.

Our stronger direction is:

```text
AI Buyer Simulation
        +
Merchant Optimization
        +
Razorpay Transaction Infrastructure
```

The real product loop becomes:

```text
SIMULATE
   ↓
UNDERSTAND
   ↓
OPTIMIZE
   ↓
EXPERIMENT
   ↓
MEASURE
   ↓
TRANSACT
   ↓
LEARN
```

The engineering philosophy remains:

```text
AI for reasoning.
Deterministic systems for truth.
Razorpay for payment execution.
Auditability for trust.
```

And the final goal is simple:

> **Build something that makes a Razorpay engineer think, "This is not just a hackathon project. I can see where this could become a real product."**

---

# 90. Sources & Research References

## Official Razorpay

1. **Razorpay AI Buildathon — official brief, tracks, evaluation framing, internship details**
   - https://razorpay.com/buildathon/

2. **Razorpay Sprint 2026 — Agentic Payments / AI-native payments direction**
   - https://razorpay.com/sprint/26

3. **Razorpay Agentic Payments — in-app, LLM and voice AI payment direction**
   - https://razorpay.com/agentic-payments/

4. **Razorpay Blog — Agentic Payments and in-app commerce**
   - https://razorpay.com/blog/agentic-payments-the-future-of-in-app-commerce/

5. **Razorpay Newsroom — Agent Studio and Agentic Experience Platform**
   - https://razorpay.com/newsroom/

---

## NPCI / UPI

6. **NPCI — UPI overview and ecosystem**
   - https://www.npci.org.in/product/upi

7. **NPCI — UPI Help Assistant**
   - https://www.npci.org.in/product/upi

8. **NPCI — Hello! UPI / conversational payments**
   - https://www.npci.org.in/product/upi/hello-upi

9. **NPCI — FiMI, domain-specific AI model for India's payment ecosystem**
   - NPCI publication, February 2026

10. **NPCI — UPI Circle / AI profile and delegated payment context**
   - NPCI UPI circulars

---

## Public Competition / Community

11. **Public GitHub project — Revenue Resilience AI**
   - https://github.com/srikrishna0603/razorpay-buildathon

12. **Revenue Resilience AI — architecture decisions**
   - https://github.com/srikrishna0603/razorpay-buildathon/blob/main/DECISIONS.md

13. **Revenue Resilience AI — review requests / implementation details**
   - https://github.com/srikrishna0603/razorpay-buildathon/blob/main/REVIEW_REQUEST.md

14. **Reddit — Razorpay AI Buildathon 2026 discussion**
   - r/Btechtards discussion

15. **Reddit — Razorpay AI Buildathon internship / track discussion**
   - r/internships discussion

16. **Reddit — Razorpay Buildathon track/competition discussion**
   - r/hackathon discussion

---

# 91. Source Quality Note

The strongest factual claims in this document come from:

```text
Razorpay official sources
NPCI official sources
Public GitHub repositories
Public community discussions
```

Where public evidence is incomplete, we have deliberately marked the conclusion as:

```text
our interpretation
our working thesis
our inference
```

We should NOT treat:

```text
estimated participant counts
rumoured competition numbers
unverified community claims
```

as facts.

The Buildathon is still ongoing, so the competitive landscape can change rapidly.

---

# 92. Document Status

```text
Track selected:
Track 01 — AI Growth & Agentic Commerce

Current project thesis:
AI Buyer Simulation + Merchant Optimization + Razorpay transaction layer

P0:
Foundation + transaction infrastructure

P1:
Core AI intelligence

P2:
Optional expansion

Primary differentiators:
- AI buyer simulation
- measurable merchant optimization
- strong safety boundary
- Razorpay-native integration
- failure handling
- auditable architecture

Current priority:
STOP RESEARCHING FOREVER.
START BUILDING.
```

---

# 93. Final Rule

We have already spent significant time choosing the track and exploring directions.

From this point onward:

```text
Research → Build
Build → Measure
Measure → Improve
Improve → Demo
Demo → Pitch
```

Not:

```text
Research
→ another idea
→ another track
→ another idea
→ another repository
→ another architecture
→ no product
```

The problem is chosen.

Now the quality of execution is the competition.

---

# 94. Current Demo vs. Future Opportunity

To protect credibility with Razorpay engineers evaluating this submission, we must explicitly bound what we are building for the hackathon versus what the full-scale architecture would require.

**Hackathon Demo (What we are building now):**
- Synchronous, stateless buyer persona evaluations
- Explicit manual overrides in the merchant dashboard
- Standard Razorpay Orders API integration

**Future Opportunity (What it would become at scale):**
- Background Celery/Redis queues for mass simulation
- Streaming updates and real-time inference
- Autonomous Pydantic models talking directly to banking APIs via MCP (Model Context Protocol)

**Why we are keeping it synchronous for the demo:**
We do NOT build a background queue for the hackathon because it obscures the deterministic API boundaries we need to prove. The hackathon priority is proving the safety model, the API contracts, and the core transactional loop. Introducing complex asynchronous infrastructure would distract from the "Wow Factor" of a deterministic, safe, and transparent AI commerce flow.


## September 4 Direction Check
- The AI Commerce control plane prioritizes analytical correctness over perceived diversity. We do NOT manipulate scoring or randomly sample the catalogue merely to make the winner distribution look diverse. Determinism is paramount.