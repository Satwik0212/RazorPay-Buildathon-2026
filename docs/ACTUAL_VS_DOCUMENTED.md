# Document 2: ACTUAL_VS_DOCUMENTED
> Reconcile every major architectural claim against actual code.

| Architectural Claim | Source | Implemented? | Reality | File Path | Line # |
|---|---|---|---|---|---|
| "Simulation evaluates full active catalogue (2,977 products)" | logic.md | VERIFIED | `get_active_catalogue_for_merchant()` retrieves 100% via outerjoin, no LIMIT | `backend/app/repositories/product_repository.py` | 58 |
| "Recommendations generated from friction evidence" | docs/features.md | VERIFIED (PARTIAL) | Yes, but logic is fully hardcoded per friction type — PRICE→10% flat, DELIVERY→2 days hardcoded, RETURN→14 days hardcoded | `backend/app/services/optimization/recommendation_service.py` | ~78 |
| "What-If is non-mutating (in-memory only)" | logic.md | VERIFIED | `modified_catalogue = copy.deepcopy(baseline_catalogue)` — WhatIfRun persists metrics but NOT product mutations | `backend/app/services/optimization/what_if_service.py` | 59 |
| "Policy engine gates all payments" | docs/architecture.md | PARTIAL | Policy engine exists for buyer agent flow, but `/buyer-personas` GET and POST have **no authentication** | `backend/app/api/v1/buyer/personas.py` | 13, 22 |
| "Authorization requires UNIQUE constraint on authorization_id" | docs/decisions.md | VERIFIED | DB-level unique constraint enforced, idempotency check in service layer | `backend/app/services/checkout_service.py` | 48 |
| "Webhook uses HMAC-SHA256 constant-time comparison" | docs/decisions.md | VERIFIED | `hmac.compare_digest(expected_sig, req.razorpay_signature)` — constant-time | `backend/app/api/v1/payments.py` | 62 |
| "LLM cannot directly mutate price/inventory/payment state" | docs/ai_integration_readiness.md | VERIFIED | LLM output (StructuredIntent) feeds into deterministic Python; campaign message is text-only | `backend/app/ai/intent_parser.py` | 18 |
| "Orders have idempotency protection" | docs/decisions.md | VERIFIED | Checks existing order by authorization_id before creation + DB UNIQUE constraint | `backend/app/services/checkout_service.py` | 48 |
| "Inventory decremented atomically on payment.captured" | docs/bugs.md BUG-001 FIXED | VERIFIED | Payment verify endpoint atomically decrements via `max(0, inv.available_quantity - item.quantity)` | `backend/app/api/v1/payments.py` | 97-101 |
| "All endpoints require authentication" | docs/safety_regulations.md | FALSE | `/buyer-personas` (GET + POST) have no auth dependency | `backend/app/api/v1/buyer/personas.py` | 13, 22 |
| "Budget conversions handled consistently (rupees vs paise)" | logic.md | VERIFIED (PARTIAL) | Catalogue search: `max_budget * 100` (intents.py:38). Custom simulation: `max_budget * 100` (simulations.py). BUT What-If modifications take `price` as raw integer with no conversion guard. | `backend/app/api/v1/buyer/intents.py` | 38 |
| "Audit trail is immutable" | docs/audit_report.md | PARTIAL | Audit events are append-only (no UPDATE/DELETE on AuditEvent). But no DB-level immutability constraint. Immutability is enforced by convention only. | `backend/app/services/audit_service.py` | - |
| "Simulation evaluates all products before truncation" | logic.md | VERIFIED | Full evaluation loop runs first; `truncate_rankings()` is called only after all metrics + recommendations are computed | `backend/app/api/v1/optimization/simulations.py` | 168, 340 |

---

## PARTIAL / FALSE Detail

### FALSE: `/buyer-personas` has no authentication

```python
# backend/app/api/v1/buyer/personas.py:13
@router.get("", response_model=List[BuyerPersonaResponse])
def list_buyer_personas(db: Session = Depends(get_db)):  # No auth dependency
    db_personas = db.query(BuyerPersona).all()
    return db_personas

@router.post("", response_model=BuyerPersonaResponse, status_code=status.HTTP_201_CREATED)
def create_buyer_persona(req: BuyerPersonaCreate, db: Session = Depends(get_db)):  # No auth
```

**Discrepancy:** Personas contain scoring weights and budget parameters used in simulation. Anyone can read or add personas without authentication.

### PARTIAL: Recommendation Logic is Fully Hardcoded

```python
# backend/app/services/optimization/recommendation_service.py
elif reason == "DELIVERY_TOO_SLOW":
    action_data = {"new_delivery_days": 2, "after_state_description": "2 days"}  # Hardcoded
elif reason == "PRICE_MISMATCH":
    action_data = {"new_price_discount_pct": 10}   # Always 10%, not computed
elif reason == "RETURN_UNCLEAR":
    action_data = {"new_return_days": 14}           # Always 14 days, not computed
```
