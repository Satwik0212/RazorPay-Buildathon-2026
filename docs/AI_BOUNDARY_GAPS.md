# Document 4: AI_BOUNDARY_GAPS
> Where AI is too loose, missing, or underutilized.

---

## A. Boundary Violations

### Violation 1: Campaign message has no structural gate

```python
# backend/app/services/optimization/campaign_service.py:73
message_content = llm_client.generate_text(prompt, system_prompt)
if not message_content or len(message_content) < 10:
    message_content = f"Special Offer! ..."  # fallback

campaign = Campaign(..., message_content=message_content)  # persisted directly
```

**Risk level: LOW.** The LLM output is stored as display text (`message_content`) and does not flow into any financial, inventory, or scoring path. However, there is no check for:
- Prompt injection echoed into campaign text
- Hallucinated product names in message
- Offensive or inappropriate content

**Deterministic gate after LLM: NO** (only `len >= 10` check).

### No violations in financial paths

`price`, `inventory.available_quantity`, `order.amount`, and `authorization.status` are ALL set by deterministic code only. LLM output never reaches these fields.

---

## B. Unused AI Capabilities

| Extracted Field | Extracted By | Used in Simulation? | Used in Search? | File |
|---|---|---|---|---|
| `category` | LLM + Offline | NO | YES (`/catalogue/search` filter) | `intents.py:52` |
| `min_budget` | LLM + Offline | NO | NO (hard constraint uses `max_budget` only) | `simulations.py` |
| `max_budget` | LLM + Offline | YES (hard constraint) | YES | `friction.py:36` |
| `requirements` | LLM + Offline | YES (hard constraint) | YES | `friction.py:42` |
| `delivery_deadline_days` | LLM + Offline | YES (hard constraint) | NO | `friction.py:55` |
| `preferences` | LLM + Offline | **NO** — extracted, never used | YES (weak text match) | not in engine.py |

**Key gap: `preferences` and `min_budget`** are parsed from natural language but silently discarded by the simulation engine. The engine would need explicit intent → persona-weight mapping to use `preferences`.

---

## C. Hardcoded Decision Logic (Where AI Could Add Value)

| Feature | Current Logic | Type | File | Line |
|---|---|---|---|---|
| Recommendation: price fix | Always suggest 10% discount | Hardcoded | `recommendation_service.py` | ~120 |
| Recommendation: delivery fix | Always set `delivery_days = 2` | Hardcoded | `recommendation_service.py` | ~150 |
| Recommendation: return fix | Always set `return_days = 14` | Hardcoded | `recommendation_service.py` | ~170 |
| Persona weights | 5 predefined, static weight vectors | Config constant | `simulations.py:22-28` | 22 |
| SCENARIO_WEIGHT_OVERRIDES | Only covers QUALITY sub-variants (5 entries) | Partial config | `simulations.py:70-107` | 70 |
| Catalogue search scoring | Hardcoded formula (30% category + 30% budget + 25% req + 15% pref) | Hardcoded | `intents.py:60-102` | 60 |
| Upsell engine | Finds highest-scoring product in same category | Deterministic | `buyer/upsell.py` | - |

---

## D. Latency / Token Estimates

| LLM Call | Est. Prompt Tokens | Est. Response Tokens | Groq Latency | Risk |
|---|---|---|---|---|
| Intent parsing (Groq) | ~300 | ~100 | ~300-600ms (10s timeout) | Adds latency to buyer search |
| Campaign generation (Groq x2) | ~150 each | ~80 each | ~300ms each | Background, not user-facing |

**Batch opportunity:** The two campaign generation LLM calls happen sequentially in a for-loop (max 3 campaigns). They could be parallelized with `asyncio` but currently use synchronous `httpx.Client`.
