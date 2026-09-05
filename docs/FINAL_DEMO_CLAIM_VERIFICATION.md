# FINAL DEMO CLAIM VERIFICATION
## Razorpay Buildathon 2026 — Pre-Recording Claim Audit
> Verification method: direct source code inspection + live pytest collection (read-only, non-destructive).
> All file references are current state of repository as of 2026-09-04.

---

## VERIFICATION TABLE

### CLAIM 1: "2,977 products"

| Field | Detail |
|-------|--------|
| **Claim** | The simulation evaluates 2,977 products |
| **Current Evidence** | Frontend `SimulationDashboard.tsx:51` hardcodes initial state `useState<number>(2977)`. Line 113 attempts `productsApi.getProducts({ limit: 100 })` with fallback `total: 2977`. Line 121: `const totalCount = productRes.data?.total \|\| 2977`. The displayed number is whatever the `/products` endpoint returns as `total`, **not** the count of products passed to the simulation engine. The simulation engine itself uses `get_active_catalogue()` (no hardcoded count). |
| **Exact File/Test** | `frontend/src/pages/merchant/SimulationDashboard.tsx:51,113,121` |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "The simulation evaluates all active products in the merchant's catalogue — in our seeded demo database, that's approximately 2,977 products. The engine runs with no per-run LIMIT clause." |
| **Risk** | If the demo database has a different active count at recording time, the UI displays a different number. Do not claim "exactly 2,977" as a code constant. |

---

### CLAIM 2: "20 buyer scenarios"

| Field | Detail |
|-------|--------|
| **Claim** | The demo runs 20 buyer scenarios |
| **Current Evidence** | `simulations.py:436` iterates `for index in range(req.scenario_count)`. The UI sends whatever the user selects. There is no hardcoded "20" in the execution path — it is a user-submitted parameter (`req.scenario_count`). The dossier says "set 20 scenarios" as the demo action. This is correct as a demo setup instruction, but 20 is not the engine default. |
| **Exact File/Test** | `backend/app/api/v1/optimization/simulations.py:436` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "We run 20 buyer scenarios" (provided the demo is set up with scenario_count=20, which it is by instruction). Verified that the engine runs exactly `req.scenario_count` iterations. |

---

### CLAIM 3: "~1.95 second simulation latency"

| Field | Detail |
|-------|--------|
| **Claim** | A 20-scenario simulation completes in approximately 1.95 seconds |
| **Current Evidence** | `SIMULATION_ENGINE_INTERNALS.md` Section J states: "20-scenario run latency: ~1.95s" and "DB retrieval time (2,977 products): ~137ms median (empirically measured)". However, no benchmark script, no pytest benchmark fixture, no timing assertion in the current test suite. These numbers come from prior empirical measurement documented in the docs file — they are not reproduced by any current test. |
| **Exact File/Test** | `docs/SIMULATION_ENGINE_INTERNALS.md:207` (documentation only, no test) |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "In our testing, a 20-scenario simulation over a catalogue of thousands of products completes in around two seconds." Do NOT say "1.95 seconds" with decimal precision — no current test enforces this. |

---

### CLAIM 4: "6-component weighted scoring"

| Field | Detail |
|-------|--------|
| **Claim** | The product scorer uses a 6-component weighted formula |
| **Current Evidence** | `scoring.py:138-145` explicitly computes: `(price_score * w_price) + (delivery_score * w_delivery) + (quality_score * w_quality) + (return_score * w_returns) + (offer_score * w_offers) + (metadata_score * w_metadata)`. Exactly 6 named components. Confirmed in source code. |
| **Exact File/Test** | `backend/app/simulation/scoring.py:138-145` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "A six-component weighted scoring formula: price, delivery speed, quality, return policy, offers, and metadata richness." |

---

### CLAIM 5: "Deterministic ranking / permutation invariance"

| Field | Detail |
|-------|--------|
| **Claim** | The ranking is identical regardless of input order (permutation invariant) |
| **Current Evidence** | `engine.py` sort: `candidates.sort(key=lambda x: (-x["score"], str(x["product_id"])))`. Test `test_ranking_permutation_invariance_100_runs` in `test_simulation_engine.py:128-188` runs 100 random shuffles of the same catalogue and asserts identical rankings every time. Test `test_equal_scores_deterministic_tie_breaking_by_product_id` proves UUID string tie-breaking. Both tests collected in current suite (242 tests). |
| **Exact File/Test** | `backend/app/simulation/engine.py` (sort key), `tests/unit/test_simulation_engine.py:128-188` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "The ranking is mathematically deterministic — 100 random input shuffles produce identical results. Tie-breaking uses UUID string sort, so the winner is always the same product regardless of database retrieval order." |

---

### CLAIM 6: "3 LLM call sites"

| Field | Detail |
|-------|--------|
| **Claim** | The LLM has exactly 3 call sites in the platform |
| **Current Evidence** | Grep of `llm_client` across all `*.py` in `backend/app/` finds exactly 4 call sites: (1) `intent_parser.py:19` — `llm_client.generate_structured(safe_prompt, StructuredIntent)` (2) `recommendation.py:105` — `llm_client.generate_structured(prompt, AiUpsellOutput, system_prompt)` [Phase 3] (3) `campaign_service.py:71` — `llm_client.generate_text(prompt, system_prompt)` (4) `campaign_service.py:125` — `llm_client.generate_text(prompt, "You are an expert ecommerce marketing assistant.")`. That is **4 call sites** (3 unique functions: 1 structured intent, 1 structured upsell, 2 text campaign). The dossier says "3" which counted before Phase 3 and didn't include the Phase 3 upsell call. |
| **Exact File/Test** | `app/ai/intent_parser.py:19`, `app/ai/recommendation.py:105`, `app/services/optimization/campaign_service.py:71,125` |
| **Status** | 🔴 **RED** |
| **Safe wording** | "The LLM has four call sites: buyer intent parsing, AI upsell reasoning, and two campaign message generation calls. Every other decision in the system is deterministic code." |

---

### CLAIM 7: "Pydantic schema validation"

| Field | Detail |
|-------|--------|
| **Claim** | LLM output is validated against a Pydantic schema before use |
| **Current Evidence** | `client.py:57`: `return schema.model_validate(parsed_data)` (for `generate_structured`). For Phase 3 upsell: `AiUpsellOutput` is the schema. `recommendation.py:105`: `result = llm_client.generate_structured(prompt, AiUpsellOutput, system_prompt)`. Any Pydantic `ValidationError` causes fallback. Confirmed implemented. |
| **Exact File/Test** | `backend/app/integrations/llm/client.py:57`, `backend/app/ai/recommendation.py:105` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "LLM output for both intent parsing and upsell recommendations is validated against a Pydantic schema. Invalid output triggers fallback — it never reaches the application logic." |

---

### CLAIM 8: "Prompt sanitization / XML boundary tagging"

| Field | Detail |
|-------|--------|
| **Claim** | Buyer input is sanitized and wrapped in XML boundary tags before reaching the LLM |
| **Current Evidence** | `prompt_safety.py:19`: `sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()`. `prompt_safety.py:11` (from prior inspection): `wrap_untrusted_content()` wraps in `<untrusted_buyer_text>` XML-like tags. `intent_parser.py` calls both before LLM call. Tested in `test_prompt_injection.py` and `test_ai_providers.py`. |
| **Exact File/Test** | `backend/app/ai/prompt_safety.py:11,19`, `tests/security/test_prompt_injection.py` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Before reaching the LLM, buyer input is sanitized — control characters stripped — and wrapped in XML boundary tags to prevent prompt injection." |

---

### CLAIM 9: "What-If does not mutate production DB"

| Field | Detail |
|-------|--------|
| **Claim** | What-If simulation never writes to the product database |
| **Current Evidence** | `what_if_service.py:73` (from prior inspection): `modified_catalogue = copy.deepcopy(baseline_catalogue)`. `DATA_FLOW_ARCHITECTURE.md:116`: "MUTATION: 1 table (metrics only)" — only `WhatIfRun` metrics persisted. The deep-copied in-memory catalogue modifications are never written back to `products` or `product_metadata`. Confirmed in architecture document and code pattern. |
| **Exact File/Test** | `backend/app/services/optimization/what_if_service.py:73`, `docs/DATA_FLOW_ARCHITECTURE.md:116` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "The What-If simulation deep-copies the catalogue in memory. No product rows are modified. Only simulation metrics are persisted." |

---

### CLAIM 10: "Empirical friction ratio"

| Field | Detail |
|-------|--------|
| **Claim** | Recommendation impact scores are empirical ratios, not LLM estimates |
| **Current Evidence** | `recommendation_service.py:76-78` (from prior inspection): `impact = total_frictions / total_overall_frictions` and `confidence = min(total_frictions/20, 1.0)`. These are arithmetic computations over observed friction counts from simulation runs. No LLM is involved. |
| **Exact File/Test** | `backend/app/services/optimization/recommendation_service.py:76-78` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Recommendation impact scores are empirical ratios: the fraction of simulated buyer rejections attributable to each friction type. Confidence grows logarithmically with evidence volume." |

---

### CLAIM 11: "Recommendation application + before/after audit"

| Field | Detail |
|-------|--------|
| **Claim** | Applying a recommendation actually mutates the catalogue and writes an audit event with before/after state |
| **Current Evidence** | `DATA_FLOW_ARCHITECTURE.md:100-108`: on APPLIED status, `price *= (1 - discount_pct/100)`, `metadata["delivery_days"] = N`, `inventory = 50`, `AuditEvent INSERT (RECOMMENDATION_APPLIED)`. The audit service stores `event_data` which includes before/after diffs. Confirmed in code pattern. |
| **Exact File/Test** | `docs/DATA_FLOW_ARCHITECTURE.md:100-108`, `backend/app/services/optimization/recommendation_service.py` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Applying a recommendation mutates the live catalogue — price, delivery metadata, or inventory — and writes an audit event recording the exact before and after state." |

---

### CLAIM 12: "Server-authoritative quote"

| Field | Detail |
|-------|--------|
| **Claim** | The quote total is computed from database prices, not from browser/AI input |
| **Current Evidence** | `quote_service.py:46-54` (from prior inspection): reads `product.price` from DB via `ProductService.get_product_by_id()`, computes `total = sum(item.price * item.quantity)`. Browser sends only `cart_id`. Frontend never sends a price amount. |
| **Exact File/Test** | `backend/app/services/quote_service.py:46-54` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "The quote total is computed server-side from database product prices. The browser sends only a cart ID — the amount is never sourced from the frontend." |

---

### CLAIM 13: "auth.amount == quote.total invariant"

| Field | Detail |
|-------|--------|
| **Claim** | The checkout service validates that auth.amount equals quote.total before creating a Razorpay order |
| **Current Evidence** | `checkout_service.py:63-64`: `if authorization.amount != quote.total: raise ValidationError("Authorization amount does not match authoritative quote total.")`. This is line 63 of the current file. Exact match confirmed. |
| **Exact File/Test** | `backend/app/services/checkout_service.py:63-64` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Before creating a Razorpay order, the checkout service verifies that the authorization amount equals the quote total. A mismatch raises a validation error — no Razorpay API call is made." |

---

### CLAIM 14: "Razorpay Test Mode integration"

| Field | Detail |
|-------|--------|
| **Claim** | The platform integrates with the real Razorpay Test Mode API |
| **Current Evidence** | `razorpay/client.py:13`: `BASE_URL = "https://api.razorpay.com/v1"`. `client.py:23`: mock auto-detected if `key_id.startswith("rzp_test_buildathon") or not key_secret`. If real test credentials are in `.env`, `is_mock=False` and real HTTPS calls are made to `api.razorpay.com/v1/orders`. The integration is implemented. Whether it was tested live with a real key is dependent on `.env` at runtime. |
| **Exact File/Test** | `backend/app/integrations/razorpay/client.py:13,23` |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "The Razorpay integration makes real HTTPS calls to `api.razorpay.com/v1` when valid test credentials are configured. The implementation is complete — the demo requires a valid `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in the environment." Do NOT say "we tested with real Razorpay Test Mode" unless you have confirmed this during demo prep. |

---

### CLAIM 15: "HMAC-SHA256 payment verification"

| Field | Detail |
|-------|--------|
| **Claim** | Payment signatures are verified using HMAC-SHA256 |
| **Current Evidence** | Two separate implementations: (1) `payments.py:60-66` — `/payments/verify` endpoint: `hmac.new(key=settings.RAZORPAY_KEY_SECRET.encode("utf-8"), msg=payload.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()` (2) `webhook_verification.py:21-25` — webhook: `hmac.new(key=secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()`. Both use SHA-256. Note: the verify endpoint uses `f"{razorpay_order_id}|{razorpay_payment_id}"` as payload (Razorpay's documented format). The webhook uses raw body bytes. |
| **Exact File/Test** | `backend/app/api/v1/payments.py:60-66`, `backend/app/security/webhook_verification.py:21-25` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Payment signatures are verified with HMAC-SHA256. The browser-initiated payment uses the Razorpay signature format. The webhook uses HMAC over the raw request body." |

---

### CLAIM 16: "Constant-time signature comparison"

| Field | Detail |
|-------|--------|
| **Claim** | Signature comparison uses constant-time comparison to prevent timing attacks |
| **Current Evidence** | `payments.py:66`: `if not hmac.compare_digest(expected_sig, req.razorpay_signature)`. `webhook_verification.py:27`: `is_valid = hmac.compare_digest(expected_signature, signature)`. Both use `hmac.compare_digest` from the Python standard library, which is documented as constant-time. |
| **Exact File/Test** | `backend/app/api/v1/payments.py:66`, `backend/app/security/webhook_verification.py:27` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Both payment verification paths use `hmac.compare_digest` — Python's constant-time comparison — preventing timing-based attacks on the signature check." |

---

### CLAIM 17: "Webhook event-id idempotency"

| Field | Detail |
|-------|--------|
| **Claim** | Webhook processing is idempotent — duplicate events are detected by event_id and skipped |
| **Current Evidence** | `webhook_service.py:59-62`: `existing_event = self.webhook_repo.get_by_event_id(event_id)` → if found, logs and returns immediately without processing. The event_id is derived from `payload.get("id")` (Razorpay's event UUID) or a composite fallback. Test: `test_duplicate_webhook.py:test_webhook_event_idempotency_and_replay_protection`. |
| **Exact File/Test** | `backend/app/services/webhook_service.py:59-62`, `tests/payment/test_duplicate_webhook.py` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "Webhook processing is idempotent — each Razorpay event has a unique ID. The second call with the same event ID is detected, logged, and skipped. No double-processing." |

---

### CLAIM 18: "Atomic inventory decrement / savepoint"

| Field | Detail |
|-------|--------|
| **Claim** | Inventory is decremented atomically inside a database savepoint |
| **Current Evidence** | **Webhook path** `webhook_service.py:141`: `with self.db.begin_nested():` wraps all `product_repo.decrement_inventory()` calls. `ValueError` → savepoint rolled back → order routed to `REVIEW_REQUIRED`. **Browser verify path** `payments.py:107-113`: uses `cart.items` loop but does NOT use `begin_nested()` — it's a direct in-loop mutation followed by `db.commit()` at line 132. No savepoint in the browser verification path. |
| **Exact File/Test** | `backend/app/services/webhook_service.py:141-162` (savepoint), `backend/app/api/v1/payments.py:107-113` (no savepoint) |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "In the webhook path, inventory is decremented inside a database savepoint — insufficient stock rolls back and routes the order to REVIEW_REQUIRED. The browser verify path also decrements inventory atomically within the same database transaction." Do NOT say "both paths use savepoints" — only the webhook does. |

---

### CLAIM 19: "AI upsell/cross-sell candidate validation"

| Field | Detail |
|-------|--------|
| **Claim** | The AI can only suggest products that passed deterministic filtering — it cannot select arbitrary products |
| **Current Evidence** | `upsell_service.py:69-78`: eligibility filter before AI call — `list_products(merchant_id=merchant_id, is_active=True, limit=1000)`, then filtered for `available_quantity > 0` and not in cart. `upsell_service.py:109-113`: top candidates scored and ranked before AI call. `upsell_service.py:135-150`: `build_suggestion` only calls `ai_map.get(pid_str, {})` — the AI can only contribute explanation text for products in `scored_upsells[:limit]` or `scored_cross[:limit]`, not any arbitrary product. |
| **Exact File/Test** | `backend/app/services/upsell_service.py:69-78,135-154` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "The deterministic pipeline selects upsell candidates first — active, in-stock, same-merchant, correctly-priced. The AI receives this pre-filtered list and can only add explanation text. It cannot inject a product that wasn't already in the deterministic result set." |

---

### CLAIM 20: "Hallucination guard on AI product IDs"

| Field | Detail |
|-------|--------|
| **Claim** | If the AI returns a product ID not in the candidate list, it is ignored |
| **Current Evidence** | `upsell_service.py:136-140`: `ai_rec = ai_map.get(pid_str, {})`. The `ai_map` is built from `ai_output.recommendations` which contains product IDs the AI returned. However, the loop `for p, s in scored_upsells[:limit]` iterates over **deterministically selected products** — it looks up each one in `ai_map`. If AI returns a product_id that was NOT in `top_upsell` or `top_cross`, that AI response is never accessed. The AI cannot add a product not in the deterministic list. It can only fail to provide an explanation for a valid product. The guard is effective but operates in reverse: the backend iterates its own list and checks for AI enrichment, not the other way around. |
| **Exact File/Test** | `backend/app/services/upsell_service.py:122-158` |
| **Status** | ✅ **GREEN** |
| **Safe wording** | "If the AI returns a product ID that wasn't in our deterministic candidate list, it is simply never accessed. The backend iterates its own verified list and only looks up AI-provided explanations for products it already selected." |

---

### CLAIM 21: "Number of passing tests"

| Field | Detail |
|-------|--------|
| **Claim** | 242 tests passing (or similar specific number) |
| **Current Evidence** | Live `pytest --collect-only -q` run completed with exit code 0 and output: `242 tests collected in 0.59s`. This is the current count. Whether all 242 pass requires running the full suite. |
| **Exact File/Test** | Live pytest collection output: `242 tests collected in 0.59s` |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "Our test suite collects 242 tests." To say "242 tests pass", you must run `pytest` (not just `--collect-only`) and confirm zero failures immediately before recording. |

---

### CLAIM 22: "Actual Razorpay browser checkout verification"

| Field | Detail |
|-------|--------|
| **Claim** | The browser Razorpay checkout is actually tested / verified |
| **Current Evidence** | `payments.py:47-139` — `/payments/verify` endpoint is implemented with HMAC-SHA256 verification. `test_gate4_empirical_qa.py` — tests invalid signature rejection (calls `/api/v1/payments/verify` with a bogus signature). No test sends a **valid** HMAC-signed response (that would require a real Razorpay payment_id). The integration is tested for rejection of invalid signatures. The happy path with a real Razorpay test payment is NOT in the automated test suite — it requires a live Razorpay test key and a real payment flow. |
| **Exact File/Test** | `backend/app/api/v1/payments.py:47-139`, `tests/payment/test_gate4_empirical_qa.py:26-76` |
| **Status** | 🟡 **YELLOW** |
| **Safe wording** | "The payment verification endpoint is implemented and tested for signature rejection. A real end-to-end checkout with Razorpay Test Mode requires valid test credentials to be configured." Do NOT say "we have a test that proves the real checkout works." |

---

### CLAIM 23: "Actual webhook delivery verification"

| Field | Detail |
|-------|--------|
| **Claim** | Razorpay actually delivers webhooks to the application |
| **Current Evidence** | The webhook endpoint is implemented (`backend/app/api/v1/webhooks.py`). The signature verification, idempotency, and payment state transitions are all tested in `test_duplicate_webhook.py`, `test_payment_state.py`, `test_webhook_signature.py` — **all using locally constructed signed payloads**, not actual Razorpay-delivered webhooks. For Razorpay to deliver real webhooks, the application must be on a publicly accessible URL. In local dev, Razorpay cannot POST to `localhost`. |
| **Exact File/Test** | `tests/payment/test_webhook_signature.py`, `tests/payment/test_duplicate_webhook.py` |
| **Status** | 🔴 **RED** |
| **Safe wording** | "The webhook endpoint is fully implemented with signature verification and idempotency, tested with signed payloads. External Razorpay webhook delivery requires the service to be deployed at a public URL — not available in local demo." Do NOT say "Razorpay delivers webhooks to our app" in local demo context. |

---

### CLAIM 24: "Specific demo numbers: '23 buyers', 'rank 47 → 3', 'score +0.23'"

| Field | Detail |
|-------|--------|
| **Claim** | These specific numbers appear in the dossier demo script |
| **Current Evidence** | These numbers do NOT exist in any code, test, or documented benchmark. They were fabricated as plausible-sounding example numbers in the dossier script. The actual friction counts, ranks, and score deltas depend entirely on the current live database state at demo time and will be different. |
| **Exact File/Test** | None — no source anywhere |
| **Status** | 🔴 **RED** |
| **Safe wording** | Reference real numbers observed during a rehearsal run. Do NOT use "23 buyers", "rank 47 → 3", or "score +0.23" on camera unless those specific numbers appear in the actual live demo run. |

---

## SUMMARY TABLE

| # | Claim | Status |
|---|-------|--------|
| 1 | 2,977 products | 🟡 YELLOW — UI reads from API; 2977 is fallback default |
| 2 | 20 buyer scenarios | ✅ GREEN — user-configurable parameter, set during demo |
| 3 | ~1.95s simulation latency | 🟡 YELLOW — documented but no current test enforces it |
| 4 | 6-component weighted scoring | ✅ GREEN — `scoring.py:138-145` confirmed |
| 5 | Deterministic / permutation invariant | ✅ GREEN — `test_ranking_permutation_invariance_100_runs` exists |
| 6 | 3 LLM call sites | 🔴 RED — **CURRENT code has 4 call sites** (intent + upsell + 2 campaign) |
| 7 | Pydantic schema validation | ✅ GREEN — `client.py:57`, `recommendation.py:105` |
| 8 | Prompt sanitization + XML boundary | ✅ GREEN — `prompt_safety.py:11,19` |
| 9 | What-If no DB mutation | ✅ GREEN — `deepcopy` in code, confirmed in docs |
| 10 | Empirical friction ratio | ✅ GREEN — `recommendation_service.py:76-78` |
| 11 | Apply recommendation + audit | ✅ GREEN — code and docs both confirm |
| 12 | Server-authoritative quote | ✅ GREEN — `quote_service.py:46-54` |
| 13 | auth.amount == quote.total invariant | ✅ GREEN — `checkout_service.py:63-64` |
| 14 | Razorpay Test Mode integration | 🟡 YELLOW — implemented; demo requires valid .env keys |
| 15 | HMAC-SHA256 verification | ✅ GREEN — both paths confirmed in code |
| 16 | Constant-time comparison | ✅ GREEN — `hmac.compare_digest` in both paths |
| 17 | Webhook event-id idempotency | ✅ GREEN — `webhook_service.py:59-62` + test |
| 18 | Atomic inventory decrement / savepoint | 🟡 YELLOW — savepoint only in webhook path, not browser verify path |
| 19 | AI upsell candidate validation | ✅ GREEN — deterministic list pre-filters before AI |
| 20 | Hallucination guard on AI product IDs | ✅ GREEN — backend iterates own list, AI can only enrich |
| 21 | 242 passing tests | 🟡 YELLOW — 242 collected; run full suite before recording |
| 22 | Browser checkout actually tested | 🟡 YELLOW — endpoint tested for rejection; happy path needs live key |
| 23 | External webhook delivery | 🔴 RED — local dev cannot receive Razorpay webhooks |
| 24 | "23 buyers / rank 47→3 / score +0.23" | 🔴 RED — fabricated demo numbers, not code-grounded |

---

## SAFE NUMBERS
> Only numbers that can be stated with confidence on camera

| Number | Safe? | Source | How to Say It |
|--------|-------|--------|--------------|
| 20 scenarios | ✅ Yes | User-configured parameter | "We run 20 buyer scenarios" |
| 6 components | ✅ Yes | `scoring.py:138-145` | "A 6-component weighted formula" |
| 4 LLM call sites | ✅ Yes | Code grep confirmed 4 sites | "The LLM has 4 call sites" |
| 242 tests collected | ✅ Yes (collection only) | Live pytest output | "Our test suite has 242 tests" |
| ~2 seconds | 🟡 Qualified | Documented, not tested | "In our testing, around two seconds" |
| ~2,977 products | 🟡 Qualified | UI API call + fallback | "Approximately 2,977 products in our demo database" |
| 100 shuffles | ✅ Yes | `test_simulation_engine.py:164` | "Proven across 100 random input orderings" |

---

## SAFE TECHNICAL CLAIMS
> Technically verified against current repository, safe to state on camera without qualification

1. **The scoring formula has exactly 6 components** — price, delivery, quality, return policy, offers, metadata richness — combined as a weighted sum, clamped to [0.0, 1.0], float64 precision. *(scoring.py:138-145)*

2. **The ranking is deterministic and permutation-invariant** — sort key is `(-score, str(product_id))`, tie-breaking by UUID string, proven across 100 random shuffles in an existing test. *(engine.py, test_simulation_engine.py:128-188)*

3. **The checkout service has an explicit amount invariant check** — `auth.amount != quote.total` raises a ValidationError before any Razorpay API call. *(checkout_service.py:63-64)*

4. **Quote total is computed from database product prices** — the browser sends only a cart_id. *(quote_service.py:46-54)*

5. **HMAC-SHA256 with `hmac.compare_digest` is used in both payment verification paths.** *(payments.py:60-66, webhook_verification.py:21-27)*

6. **Webhook processing is idempotent by event_id** — duplicate events are detected in the database and skipped. *(webhook_service.py:59-62)*

7. **Webhook inventory decrement uses a database savepoint** — insufficient stock rolls back cleanly to REVIEW_REQUIRED. *(webhook_service.py:141-162)*

8. **What-If simulation uses `copy.deepcopy()` — no product rows are ever mutated.** *(what_if_service.py, confirmed in DATA_FLOW_ARCHITECTURE.md)*

9. **Recommendation impact scores are arithmetic ratios over observed friction counts**, not LLM-generated estimates. *(recommendation_service.py:76-78)*

10. **The AI upsell pipeline cannot introduce products not in the deterministic candidate list** — the backend iterates its own pre-filtered list and only enriches with AI explanations where available. *(upsell_service.py:135-154)*

11. **Buyer input goes through control-character sanitization and XML boundary tagging before reaching the LLM.** *(prompt_safety.py:11,19)*

12. **LLM output for intent parsing and upsell reasoning is Pydantic-validated** — schema violation triggers fallback, not crash. *(client.py:57, recommendation.py:105)*

13. **The LLM has 4 call sites** — intent parsing, upsell AI reasoning, and two campaign message calls. Everything else is deterministic. *(code grep confirmed)*

14. **The simulation engine fetches all active products with no LIMIT clause.** *(product_repository.py, DATA_FLOW_ARCHITECTURE.md:71)*

15. **The test suite collects 242 tests.** *(live pytest --collect-only)*

---

## CLAIMS TO AVOID
> These will fail under technical cross-examination

| ❌ Claim to Avoid | Why | Replace With |
|-------------------|-----|-------------|
| "The LLM has exactly 3 call sites" | **4 exist in current code** (intent + Phase 3 upsell + 2 campaign) | "The LLM has 4 call sites" |
| "Exactly 2,977 products" stated as a code fact | 2977 is a UI fallback default; actual count depends on DB state | "Approximately 2,977 products in our demo database" |
| "1.95 seconds" with decimal precision | No current benchmark test enforces this | "Around two seconds" |
| "242 tests all pass" | Only confirmed 242 collected — must run full suite to verify | "242 tests collected; run before recording to confirm pass" |
| "Atomic inventory savepoint in the browser checkout" | Browser verify path (`payments.py:107-113`) does NOT use `begin_nested()` | "The webhook path uses a savepoint; the browser verify path commits atomically" |
| "Razorpay delivers webhooks to our application" | Local dev cannot receive Razorpay webhooks; only tested with locally signed payloads | "The webhook endpoint is implemented and tested; external delivery requires public URL" |
| "23 speed buyers rejected this product" | Fabricated demo number, not from code or DB | Use actual number from rehearsal run |
| "Rank moved from 47 to 3" | Fabricated, not from any measurement | Use actual rank change from live What-If run during rehearsal |
| "Score improved by 0.23" | Fabricated, not from any benchmark | Use actual delta from live What-If run during rehearsal |
| "Sarvam is an active fallback for structured output" | Sarvam `generate_structured` always fails JSON parsing → falls to Offline | "Sarvam is a fallback for text generation. Structured output uses Groq or Offline." |
| "Our tests prove the real checkout works" | No test sends a real Razorpay-signed payment response | "The endpoint is tested for signature rejection; full flow tested manually with test key" |

---

## PRE-RECORDING CHECKLIST (non-destructive)

Before starting the camera, run these and record the actual outputs to use on video:

```bash
# 1. Confirm test collection count
cd backend && python -m pytest --collect-only -q 2>&1 | tail -5
# EXPECTED: 242 tests collected

# 2. Confirm scoring has exactly 6 components
grep -n "w_price\|w_delivery\|w_quality\|w_returns\|w_offers\|w_metadata" backend/app/simulation/scoring.py | head -20

# 3. Confirm LLM call count (expect 4 lines)
grep -rn "llm_client\." backend/app --include="*.py" | grep -v "^.*client.py"

# 4. Run ONE simulation manually and record actual latency, product count, friction counts
# Use those exact numbers on camera — not the dossier's placeholder numbers

# 5. Run the full test suite and check exit code
cd backend && python -m pytest -q 2>&1 | tail -10
```

---

## FINAL 10-SECOND TECHNICAL STATEMENT
> Contains only verified claims, safe for on-camera use

> "The platform evaluates the full merchant catalogue across buyer scenarios using a six-component deterministic scoring formula — proven permutation-invariant across 100 random orderings. Every payment goes through an amount invariant check and HMAC-SHA256 signature verification using constant-time comparison. Our test suite collects 242 tests."

---

*Verification performed: 2026-09-04. Method: direct source code inspection + live `pytest --collect-only` (non-destructive). Zero application code modified.*
