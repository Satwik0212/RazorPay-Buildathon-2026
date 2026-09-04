# Razorpay AI Commerce Platform - Project Context & Index

This document serves as the root entry point for understanding the Razorpay AI Commerce Platform (Buildathon 2026). It contains all context necessary for an AI agent or new engineer to navigate the project.

## 1. Project Objective
We are building a two-sided AI-native commerce layer:
1. **AI Buyer**: A conversational intent-parsing agent that can discover products, match strict constraints (budget, delivery, quality), and complete a Razorpay payment seamlessly.
2. **Merchant AI Control Center**: A backend control plane where merchants can run deterministic simulations across their full catalogue, identifying exactly why AI buyers are dropping off (frictions) and applying data-backed recommendations (price cuts, restocking, metadata enrichment) to optimize their "AI Readiness".

The core principle is **"CODE is the ultimate source of truth."** The AI models propose and interpret intent, but the backend strictly gates execution based on deterministic math (Scoring, Constraints, and Payments).

## 2. Tech Stack
**Frontend (`/frontend`)**:
- React 19 (TypeScript)
- Vite 5
- TailwindCSS 4
- React Router DOM 7
- Recharts (for Analytics)
- State management: React Context & Hooks
- Network: Axios

**Backend (`/backend`)**:
- Python 3.12
- FastAPI (REST API)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Database)
- Pydantic v2 (Validation)
- Razorpay API (Payment execution)
- Pytest (Testing)

## 3. The Documentation Ecosystem
The `/docs` directory is comprehensive and up-to-date. If you want to investigate how something works, refer to these canonical documents *first*:

1. **`logic.md`** - **Start here for logic.** Contains the exact formulas, sources, edge cases, and deterministic rules for all metrics (Scoring, Hard Constraints, Recommendations, What-If Simulator, Payment Amounts).
2. **`architecture.md`** - The high-level system components, synchronous flow, and entity relationships.
3. **`api_contracts_and_api_plan.md`** - The complete REST API surface, schemas, idempotency guarantees, and P0/P1/P2 boundaries.
4. **`database.md`** - The PostgreSQL schema definitions and field-level sources of truth.
5. **`bugs.md`** - Verified, reproducible bugs currently active or recently fixed in the system.
6. **`features.md`** - The status of features (Implemented, Planned).
7. **`DECISIONS.md`** - Architectural decisions (e.g., Full-catalogue in-memory simulation, deterministic sorting).

## 4. Key Architectural Behaviors (Do Not Deviate)
1. **No Fake Data**: If a product has no inventory mapped, it returns `None`. We never `COALESCE` with arbitrary numbers (like 10).
2. **Full-Catalogue Simulation**: The simulation evaluates **100%** of a merchant's active catalogue (e.g., 2,977 products) deterministically in Python before any ranking or truncation occurs.
3. **Idempotency**: Orders and webhook states are strictly enforced via DB unique constraints.
4. **Deterministic Ranking**: Scoring and Tie-breaking use float64 math and UUID sorting without LLM involvement.
5. **Payload Bounding**: Truncate API arrays (e.g., max 31 candidate products returned) *only after* full-catalogue metrics are calculated.

## 5. Local Setup
**Backend**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pytest backend/tests/
uvicorn app.main:app --reload
```
**Frontend**:
```bash
cd frontend
npm install
npm run dev
```
