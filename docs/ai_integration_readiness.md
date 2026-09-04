# AI Integration & External API Readiness

> **Module Owner:** Sanji (AI + Buyer Simulation + Optimization Engineer)
> **Status:** REAL AI INTEGRATED (Groq Primary, Sarvam Fallback)
> **Test Pass Rate:** 60/60 PASS
> **Last Update:** 2026-08-29

---

## 1. AI Architecture Map

```text
Customer / Buyer Prompt (Natural Language)
        ↓
POST /api/v1/buyer/intents
        ↓
PromptSafety Sanitization (XML Boundary Wrapping: <untrusted_buyer_text>)
        ↓
IntentParser (backend/app/ai/intent_parser.py)
        ↓
LLMClient Adapter (backend/app/integrations/llm/client.py)
        ├── 1. GroqProvider (Primary - Llama3 API)
        ├── 2. SarvamProvider (Fallback - Sarvam API)
        └── 3. OfflineProvider (Emergency Fallback - Regex Parser)
        ↓
Structured Intent Validation (StructuredIntent / BuyerIntent Pydantic Schema)
        ↓
┌────────────────────────────────────────────────────────────────────────┐
│                   DETERMINISTIC OFF-LINE BACKEND LOOP                  │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Catalogue Search: ProductService + PostgreSQL DB Query              │
│ 2. Candidate Filtering: Hard constraints (Budget, Stock, Requirements)  │
│ 3. Persona Scoring: ProductScorer (Multi-attribute feature math)      │
│ 4. Ranking & Selection: SimulationEngine (Rank #1 Selection)           │
│ 5. Friction Evaluation: FrictionDetector (Hard & Soft Friction)        │
│ 6. Recommendation Generator: RecommendationService (Evidence-based)  │
│ 7. What-If Optimization: WhatIfService (In-memory clone simulation)   │
└────────────────────────────────────────────────────────────────────────┘
```

The AI layer strictly decouples unstructured natural language interpretation from core commerce operations. The LLMs perform intent translation (`IntentParser` \(\rightarrow\) `LLMClient`), while all financial, scoring, simulation, and recommendation evaluations run 100% deterministically in Python.

---

## 2. External Providers Strategy

| Provider | Role | SDK / Integration |
| :--- | :--- | :--- |
| **Groq** | PRIMARY | HTTPX `httpx.post` API calls (fastest Llama3-8b processing). |
| **Sarvam** | FALLBACK | HTTPX `httpx.post` API calls (called seamlessly on Groq failure). |
| **Offline** | EMERGENCY | Native Python Regex extraction (100% offline, guaranteed uptime). |

---

## 3. Required Credentials & Environment Variables

Required variables defined in `backend/app/core/config.py` and `.env.example`:

```ini
# LLM Integration Settings (Sanji Module)
GROQ_API_KEY=
SARVAM_API_KEY=
```

**No external credentials belong in git.** `api-keys` must be injected locally via `.env` or CI/CD pipelines.

---

## 4. Features Requiring External AI

The system requires an LLM API key for:
1. **Open-Ended Natural Language Intent Parsing:** Accurately translating complex, multi-clause natural language queries into structured `StructuredIntent` formats (beyond regex capacities).

---

## 5. Fallback Behavior & Emergency Mode

The system features graceful, seamless provider failure degradation:
- The system attempts **Groq**.
- If Groq fails (network error, API limit, missing key, malformed unstructured JSON), the system falls back to **Sarvam**.
- If Sarvam fails, the system triggers the **Emergency OfflineProvider**, deploying localized Regex semantic extraction to keep commerce flows uninterrupted.

Running with `GROQ_API_KEY=""` and `SARVAM_API_KEY=""` enables the fully local application.

---

## 6. Security Boundary Audit

| Safety Principle | Implementation | Status |
| :--- | :--- | :---: |
| **No Hardcoded Secrets** | Credentials read strictly from `Settings` / `.env`. `.env` ignored in `.gitignore`. | **PASSED** ✅ |
| **Financial Boundary Isolation** | LLM outputs are wrapped in `StructuredIntent`. The LLM **cannot** set cart totals, authorize quotes, issue refunds, or create Razorpay orders. | **PASSED** ✅ |
| **Prompt Injection Protection** | Raw buyer text is wrapped in `<untrusted_buyer_text>` XML tags and sanitized via `PromptSafety`. Attacks cannot break Pydantic structure. | **PASSED** ✅ |
| **Zero Side Effects** | Simulation & What-If evaluation run purely in memory without mutating database or financial state. All outputs tagged `SIMULATED RESULT`. | **PASSED** ✅ |

---

## 7. Current Tests

- 6 new tests added for AI Provider fallback routing, mocking out real LLM API calls and evaluating failure paths.
- LLM security boundaries and prompt injection remain thoroughly tested and contained.
- **Total Test Suite Result:** **60 / 60 PASSED** (100% pass rate).

---

## 8. Setup & Demo Readiness

To run the application locally or in a demo environment:
1. Add `GROQ_API_KEY` and `SARVAM_API_KEY` to `.env`.
2. Start the backend.
3. Natural language queries will now leverage the Groq LLM API.
4. Omitting the keys will seamlessly engage the Deterministic Offline engine.


## September 4 Update: Simulation Precision
- AI boundaries remain strict. Simulation engine scores and ranks are 100% deterministic using Python. LLM is not used for sorting, tie-breaking, or metadata normalization.