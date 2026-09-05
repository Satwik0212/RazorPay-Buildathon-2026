# GraahakLens: Agentic Commerce Platform

> **An AI buyer simulation and optimization layer that helps merchants understand how AI buyers evaluate their catalogue, fix conversion friction, and complete purchases through Razorpay.**

![Razorpay Buildathon](https://img.shields.io/badge/Razorpay-Buildathon_2026-blue.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)
![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)
![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791.svg)

---

## 1. The Problem

AI agents are rapidly becoming the primary shopping intermediaries between consumers and merchants. However, traditional merchant analytics tell merchants what happened in the past, not *how an AI buyer reasons* about their catalogue right now.

Product discovery today depends on complex constraints: price fit, delivery speed, compatibility, implicit features, and offer configurations. When an AI agent drops a product from consideration, the merchant is completely blind to the exact point of friction.

Merchants need a way to test their catalogue's readiness against AI buyer logic before they lose real commercial opportunities. Existing checkout systems execute transactions beautifully but do not provide this critical AI buyer readiness and explanation layer.

**Being online is not the same as being AI discoverable, AI selectable, and AI purchasable.**

---

## 2. What the Product Does

GraahakLens bridges the gap between merchant catalogues and AI buyers through a comprehensive, dual-sided architecture:

### Merchant Optimization Side
Merchants can seamlessly ingest massive catalogues (including unstructured CSVs) using AI-assisted schema mapping. Once ingested, they can run **AI Buyer Simulations** against their active catalogue. The system deterministically evaluates every product, identifies exact friction points (e.g., poor return policy, slow delivery), and issues evidence-based recommendations. Merchants can preview changes via a safe **What-If** simulation, apply the fixes, and instantly see their competitive score increase.

### AI Buyer Side
Buyers (or simulated AI intent agents) express natural language shopping intents. The system parses these intents into structured constraints, deterministically evaluates and scores the catalogue, and drives product selection. The flow seamlessly handles AI-reasoned upsells and cross-sells, transitioning into an authoritative cart, server-generated quote, and secure **Razorpay Test Mode** checkout.

---

## 3. Feature Matrix

| Feature | What it does | Why it matters |
|---------|--------------|----------------|
| **AI Buyer Simulation** | Evaluates the merchant's catalogue against synthetic buyer personas. | Shows merchants exactly how they rank against AI agents. |
| **Deterministic Catalogue Evaluation** | Filters and scores all active products via hard backend rules. | Prevents AI hallucinations from skewing product visibility. |
| **Six-Dimensional Scoring** | Scores Price, Delivery, Quality, Returns, Offers, and Metadata. | Provides granular, actionable insights into product competitiveness. |
| **Buyer Reasoning** | Explains exactly why a product won or was disqualified. | Removes the black box of AI product selection. |
| **Friction Detection** | Flags specific thresholds (e.g., "delivery too slow") causing drop-offs. | Identifies the lowest hanging fruit for conversion optimization. |
| **Evidence-Based Recommendations** | Suggests precise changes backed by aggregate friction data. | Ensures merchants only act on real observed problems. |
| **What-If Simulation** | Re-runs the simulation with hypothetical changes applied. | Proves the ROI of a change before modifying the live database. |
| **AI Catalogue Normalization** | Maps unknown merchant CSV schemas to canonical formats via LLM. | Makes onboarding thousands of products frictionless and fast. |
| **AI Upsell / Cross-Sell** | Analyzes cart state to reason about and suggest logical additions. | Increases average order value dynamically and intelligently. |
| **Server Authoritative Quotes** | Computes the final payable amount strictly on the backend. | Prevents browser-side price tampering. |
| **Razorpay Test Mode** | Executes the payment flow through Razorpay's standard checkout. | Completes the commerce loop securely. |
| **Webhook Idempotency** | Safely processes Razorpay payment.captured events via HMAC SHA256. | Guarantees exact once transaction processing. |
| **Database Enforced Ownership** | Isolates all products, carts, and simulations by merchant_id. | Strictly prevents cross-tenant data leakage. |

---

## 4. End-to-End Flow

`mermaid
flowchart TD
    subgraph Merchant Loop
        M[Merchant] -->|Upload CSV| Ingest[AI Catalogue Ingestion]
        Ingest --> DB[(PostgreSQL)]
        M -->|Trigger| Sim[AI Buyer Simulation]
        Sim --> Fric[Friction Detection]
        Fric --> Rec[Evidence Recommendations]
        Rec --> WhatIf[What-If Simulation]
        WhatIf --> Apply[Apply to Catalogue]
        Apply --> DB
    end

    subgraph Buyer Loop
        B[AI Buyer Intent] --> Parse[LLM Intent Parsing]
        Parse --> Filter[Deterministic Filtering & Scoring]
        DB --> Filter
        Filter --> Cart[Add to Cart]
        Cart --> Up[AI Upsell / Cross Sell]
        Up --> Quote[Server Authoritative Quote]
        Quote --> RZ[Razorpay Checkout]
        RZ -->|Webhook| Hook[HMAC Validation & Idempotency]
        Hook --> Audit[Transaction & Audit Logging]
    end
`

---

## 5. Architecture

The system operates on a fundamental principle: **"The LLM proposes. Deterministic backend logic decides."**

* **Frontend asks:** The React SPA issues commands.
* **API validates:** FastAPI routes strictly validate incoming shapes via Pydantic and authenticate via JWT.
* **LLM translates:** Natural language is converted into structured JSON constraints via OpenAI-compatible endpoints.
* **Services decide:** Deterministic backend rules (not the LLM) filter out-of-budget products, rank them, and enforce policy.
* **Database preserves:** PostgreSQL ensures transactional consistency, ownership boundaries, and referential integrity.
* **Razorpay executes:** The payment is handled by Razorpay's external infrastructure.
* **Webhook confirms:** The server receives the webhook, verifies the HMAC SHA256 signature in constant time, and safely transitions state.
* **Audit records:** Every critical action is immutably written to an audit log.

---

## 6. Architectural Highlights

* **Full Active Catalogue Evaluation:** The simulation engine evaluates all active products without artificial truncation limits.
* **Permutation Invariant Scoring:** The scoring engine mathematically guarantees that product evaluation is order-independent.
* **Structured LLM Outputs:** Pydantic is used extensively to coerce LLM responses into rigid formats.
* **Candidate Filtering Before AI:** Upsell candidates are pre-filtered based on deterministic inventory and category compatibility *before* the LLM sees them, protecting against hallucinations.
* **Server Authoritative Quote:** The browser cannot supply the payment amount. It requests a quote ID; the backend looks up the cart, sums the canonical DB prices, and locks the quote.
* **Constant Time Signature Comparison:** Razorpay webhook verification uses hmac.compare_digest to prevent timing attacks.
* **Database Enforced Ownership:** All queries implicitly join on the authenticated merchant_id.
* **What-If Isolation:** Hypothetical catalogue mutations exist entirely in memory during the simulation run and are never committed to the database.

---

## 7. AI Architecture

To maintain strict security and predictability, AI is restricted to highly specific boundaries. **There are exactly 4 LLM call sites in the entire architecture:**

1. **Buyer intent parsing** (intent_parser.py)
2. **Upsell/cross-sell reasoning** (ecommendation.py)
3. **Catalogue schema mapping** (i_mapper.py)
4. **Campaign generation** (campaign_service.py)

**The Pipeline:**
LLM String → Structured Output → Pydantic Validation → Deterministic Backend Logic

**Where AI is intentionally NOT used:**
* **Ranking is deterministic:** The LLM does not arbitrarily sort products.
* **Pricing is deterministic:** The LLM cannot invent a price.
* **Payment amounts are deterministic:** The LLM cannot authorize discounts.
* **Persistence is deterministic:** The LLM cannot execute raw SQL or directly mutate state.

This clear separation of AI reasoning and business decision-making represents the strongest engineering discipline in the project.

---

## 8. AI Buyer Simulation Engine

The simulation engine evaluates merchant products against synthetic personas using a robust **Six-Dimensional Scoring Model**:

1. **Price Fit:** How well the product aligns with the buyer's budget benchmark.
2. **Delivery / Speed Fit:** Feasibility of meeting buyer urgency.
3. **Quality & Brand Fit:** Based on ratings and brand sentiment.
4. **Return Policy Fit:** Alignment with buyer risk tolerance.
5. **Offer & Discount Fit:** Responsiveness to deals.
6. **Metadata & Feature Richness:** Completeness of the catalogue entry.

By deterministically combining these dimensions using persona-specific weights, the system accurately mimics human/AI purchasing trade-offs without requiring slow, expensive LLM calls for every product row.

---

## 9. Explainability & The Merchant Optimization Loop

Instead of generating unsupported LLM commentary, GraahakLens derives explainability mathematically. Merchants see exact decision drivers (e.g., "Disqualified: Price exceeded maximum budget of ₹500").

**The Optimization Loop:**
1. **Simulation:** Runs thousands of simulated buyer checks.
2. **Friction:** Aggregates dropped products (e.g., 50 failures due to delivery).
3. **Recommendation:** Issues a fix based on *observed evidence*.
4. **What-If:** In-memory simulation of the catalogue with the fix applied.
5. **Apply:** Mutates production state only upon merchant confirmation.

---

## 10. Catalogue Ingestion & AI Normalization

GraahakLens handles mass catalogue ingestion using a dual-path pipeline:
* **Known Schemas:** Bypasses AI for a deterministic fast path (e.g., Flipkart format).
* **Unknown Schemas:** An LLM maps unknown CSV headers to the canonical database schema.

**"AI maps the schema. The backend owns the data."**
The LLM never extracts data directly. It only provides a structural mapping. The backend deterministically processes rows, runs business validation, identifies errors, and forces the merchant to review and resolve conflicts before persisting.

---

## 11. Razorpay Integration

The payment architecture guarantees commercial integrity:

1. **Cart:** Buyer adds a validated product.
2. **Server Quote:** Backend locks the cart, checks inventory, reads canonical prices, and issues a Quote.
3. **Razorpay Test Order:** The backend calls Razorpay API to generate an order_id for the exact Quote amount.
4. **Checkout:** The frontend opens Razorpay Checkout using the locked order_id.
5. **Payment Verification:** Razorpay fires a webhook.
6. **Transaction & Audit:** Backend verifies the HMAC signature, confirms idempotency, updates inventory, and commits an audit log.

*Note: All transactions run in Razorpay Test Mode. No real money is processed.*

---

## 12. Security Model

* **Authentication:** Stateless JWT bearer authentication. /auth/me serves as the authoritative source of identity.
* **Authorization (RBAC):** Strict isolation between MERCHANT and CUSTOMER roles. A customer cannot access merchant analytics; a merchant cannot delete another merchant's products.
* **Data Isolation:** No trust is placed in client-submitted merchant IDs. All relationships use backend-derived identity.
* **Payment Security:** Server-authoritative quote calculations. External webhook validation.
* **AI Security:** Prompt injection protection mechanisms, structured output boundaries, and strict candidate allowlists prevent malicious intent from altering the commercial state.

---

## 13. Database / Data Model

The application uses PostgreSQL with SQLAlchemy ORM.

`mermaid
erDiagram
    MERCHANT ||--o{ PRODUCT : owns
    MERCHANT ||--o{ CATALOGUE_IMPORT_JOB : runs
    MERCHANT ||--o{ SIMULATION_RUN : executes
    SIMULATION_RUN ||--o{ SIMULATION_RESULT : contains
    SIMULATION_RUN ||--o{ OPTIMIZATION_RECOMMENDATION : produces
    
    CUSTOMER ||--o{ CART : owns
    CART ||--o{ CART_ITEM : contains
    CART ||--o| QUOTE : generates
    QUOTE ||--o| ORDER : authorizes
    ORDER ||--o| PAYMENT : processed_as
    
    PRODUCT ||--o{ CART_ITEM : added_to
`

**Key Constraints:**
* Products, Inventory, and Simulations are strictly bound to their parent Merchant.
* Razorpay payment IDs and webhook event IDs are strongly enforced as unique to prevent replay attacks.
* Money is stored flawlessly as integer minor units (paise).

---

## 14. API Architecture

The system exposes a rich, RESTful FastAPI interface under /api/v1/:

* /auth: Registration, Login, Profile
* /catalogue: AI Import, Mapping, Resolution
* /merchants: Merchant management
* /products: Active catalogue CRUD
* /carts: Basket management
* /quotes: Quote generation & locking
* /checkout: Razorpay order creation
* /payments: Payment fetching
* /webhooks: Razorpay event consumption
* /optimization/simulations: Persona runs
* /optimization/recommendations: What-if logic
* /buyer: Agentic intent, Upsells, Cross-sells
* /analytics: Real-time dashboard stats
* /authorizations, /policies, /audit: Platform internals

---

## 15. Testing & Validation

The repository demonstrates engineering maturity with a comprehensive test suite.
* **Total backend tests:** ~330 (Integration, Unit, and Security boundaries)
* **Status:** Passing.

**High-Value Tests Implemented:**
* Cross-merchant isolation (ensuring 403/404 on adversarial access attempts).
* Payment amount tampering protection.
* Duplicate webhook idempotency.
* Invalid signature rejection.
* P0 DB integrity checks covering the complete E2E optimization loop.
* Permutation invariance for the scoring engine.

---

## 16. Performance / Scale

* The backend simulation engine can evaluate the entire active catalogue without explicit arbitrary limits using fast numerical matrix-style scoring calculations.
* In our testing, evaluating intents against a demo database of **2,977 active products** successfully completes in approximately **2-3 seconds**. 
* *(Note: These are observed metrics during testing, not formal large-scale distributed benchmarks).*

---

## 17. Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React, Vite, TS, Tailwind | High-performance, statically typed SPA UI. |
| **Backend** | FastAPI, Python 3.12 | Async backend handling core API logic. |
| **Database** | PostgreSQL, SQLAlchemy, Alembic | ACID-compliant persistence and migrations. |
| **AI / LLM** | Groq API Wrapper (OpenAI compatible) | Fast, structured generation using open models. |
| **Payments** | Razorpay SDK | Test Mode quote & checkout handling. |
| **Testing** | pytest, pytest-asyncio | Robust unit, integration, and security tests. |

---

## 18. Project Structure

`	ext
├── backend/
│   ├── app/
│   │   ├── ai/            # Intent parsing, LLM wrappers
│   │   ├── api/v1/        # FastAPI routes
│   │   ├── core/          # Config, Security, DB session
│   │   ├── ingestion/     # AI catalogue normalizers
│   │   ├── integrations/  # Razorpay and LLM clients
│   │   ├── models/        # SQLAlchemy ORM definitions
│   │   ├── schemas/       # Pydantic validation boundaries
│   │   ├── services/      # Deterministic domain logic
│   │   └── simulation/    # Deterministic scoring engine
│   ├── migrations/        # Alembic database schemas
│   └── tests/             # 330+ pytest suite
├── frontend/
│   ├── src/
│   │   ├── api/           # Axios interceptors
│   │   ├── components/    # Feature-scoped UI components
│   │   ├── layouts/       # Guarded auth routing
│   │   ├── pages/         # High-level views
│   │   └── types/         # TypeScript interfaces
├── docs/                  # Audit verification dossiers
└── README.md              # You are here
`

---

## 19. Engineering Principles

1. **AI proposes, deterministic systems decide.**
2. **The browser is never trusted with financial authority.**
3. **The backend is the absolute authority for identity and ownership.**
4. **What-If simulations never mutate production state.**
5. **Every external payment state transition is strictly verified.**
6. **Recommendations must be grounded in observed data, not hallucinations.**
7. **All critical commercial workflows must be immutably auditable.**

---

## 20. Design Tradeoffs

We intentionally **did not** introduce Microservices, Kafka, Redis, or Vector Databases. 

**Why?**
The system favors a modular service monolith with deterministic domain logic backed by relational PostgreSQL because it provides:
* Lower operational complexity.
* Unbreakable transactional consistency.
* Immediate auditability across tables.
* A perfect fit for a synchronous, closed-loop AI agent simulation requiring immediate response times.

---

## 21. What Makes This Different

* **Generic AI Chatbot vs GraahakLens:** Chatbots talk to users. GraahakLens mathematically simulates how AI evaluates catalogues, empowering merchants to fix issues *before* the chatbot rejects their product.
* **Generic Recommendations vs Evidence-Backed:** Our system doesn't guess. If delivery speed caused 80 product rejections in simulation, the recommendation focuses on delivery speed.
* **Generic CSV Upload vs AI Schema Mapping:** Instead of forcing merchants into strict templates, our AI maps their arbitrary CSV headers to our canonical database schema, and deterministic validation handles the rest.

---

## 22. Demo Flow

1. **Login as Merchant** to view the active catalogue.
2. **Upload a CSV** using the AI ingestion tool to map schema headers and resolve validation errors.
3. **Run AI Buyer Simulation** to watch synthetic personas evaluate the catalogue.
4. **Inspect Fiction** to see exactly why products won or lost (e.g., price too high).
5. **Open a Recommendation** and trigger a **What-If simulation** to prove the ROI of lowering the price.
6. **Apply the fix** directly to the catalogue.
7. **Switch to Buyer View**, express a natural language intent, and watch the deterministic engine correctly discover the newly optimized product.
8. Add to cart, view an **AI Upsell**, and generate a secure **Quote**.
9. Complete the **Razorpay Test Mode** checkout.
10. Check the backend audit logs to verify idempotency and success.

---

## 23. Local Setup

**Environment Requirements:** Python 3.12+, Node.js 18+, PostgreSQL.

1. **Database Setup**
   `ash
   createdb razorpay_buildathon
   `
2. **Backend Startup**
   `ash
   cd backend
   python -m venv venv
   source venv/bin/activate  # (or venv\Scripts\activate on Windows)
   pip install -r requirements.txt
   alembic upgrade head
   python check_db.py  # (Optional: Seeds initial data)
   uvicorn app.main:app --reload
   `
3. **Frontend Startup**
   `ash
   cd frontend
   npm install
   npm run dev
   `

---

## 24. Environment Variables

Create a .env file in the ackend/ directory.

| Variable | Required | Purpose |
|----------|----------|---------|
| DATABASE_URL | Yes | PostgreSQL connection string. |
| JWT_SECRET_KEY | Yes | Cryptographic key for signing auth tokens. |
| GROQ_API_KEY | Yes | Access to the OpenAI-compatible LLM endpoint. |
| RAZORPAY_KEY_ID | Yes | Merchant Razorpay Test Mode Key. |
| RAZORPAY_KEY_SECRET | Yes | Merchant Razorpay Test Mode Secret. |

*(Note: Never commit secret values to version control. Reference ackend/.env.example)*

---

## 25. Limitations / Honest Scope

* **Test Mode Only:** The Razorpay integration strictly uses Test Mode. No real money is processed.
* **Webhook Reachability:** Full external Razorpay webhook delivery verification requires a publicly reachable endpoint (e.g., ngrok) during local testing.
* **Simulation Scope:** The simulated buyer personas represent a mathematically controlled abstraction, not a claim about every real-world arbitrary AI agent.
* **LLM Constraints:** LLM reasoning is heavily constrained by deterministic business logic. This is an intentional security design, not an oversight.
* **Performance Numbers:** Mentioned simulation latencies are local testing observations, not formal distributed benchmarks.

---

## 26. Roadmap

* **Richer Catalogue Signals:** Support for multi-variant products, live stock thresholds, and multi-currency quotes.
* **More Buyer Personas:** Introduce highly specific niche personas (e.g., "Eco-conscious bulk buyer").
* **Broader Optimization Actions:** Direct integrations with external logistics partners to simulate delivery adjustments automatically.
* **Expanded AI Shopping Protocols:** Provide API endpoints strictly designed for autonomous AI agents to query the catalogue directly.

---

**From asking whether a catalogue is ready for AI buyers, to proving it through a securely verified Razorpay checkout—GraahakLens closes the loop between AI product discovery and modern agentic commerce.**
