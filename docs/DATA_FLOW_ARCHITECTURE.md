# Document 3: DATA_FLOW_ARCHITECTURE
> Text-only flowcharts. No prose explanations.

---

## Buyer Flow

```
POST /buyer/intents  (req.text: str)
  → PromptSafety.sanitize_input()          [deterministic, backend/app/ai/prompt_safety.py:17]
  → PromptSafety.wrap_untrusted_content()  [deterministic, prompt_safety.py:11]
  → LLMClient.generate_structured()        [AI, integrations/llm/client.py:313]
      → GroqProvider (primary)             [probabilistic, client.py:14]
      → SarvamProvider (fallback)          [probabilistic, client.py:95]
      → OfflineProvider (emergency)        [deterministic regex, client.py:185]
  → StructuredIntent (Pydantic validated)  [deterministic gate, schemas/buyer/intent.py:9]
  → BuyerIntentResponse returned           [NO DB write, NO inventory mutation]

POST /catalogue/search  (req: CatalogueSearchRequest from StructuredIntent)
  → req.max_budget * 100                  [deterministic rupee→paise, intents.py:38]
  → ProductService.list_products(limit=50) [SQL, repositories/product_repository.py:20]
      MUTATION: none (read-only)
  → Hard filter: price <= max_price        [deterministic, intents.py:52]
  → Soft scoring per product               [deterministic match_score formula, intents.py:60-100]
  → Sort by match_score desc              [deterministic]
  → CatalogueSearchResponse (50 products) [NO DB write]

POST /carts/{merchant_id}/items  (customer adds chosen product)
  → CartRepository.add_item()             [DB WRITE: cart_items table]
      MUTATION: cart_items INSERT

POST /quotes  (customer locks price)
  → QuoteService.create_quote()           [DB READ: products (authoritative price)]
      MUTATION: quotes INSERT
      price = product.price * quantity    [deterministic, quote_service.py:55]
      total = subtotal - 0 + 0 + 0        [tax/shipping/discount all 0 currently]
      quote_hash = HMAC of cart snapshot  [deterministic, idempotency.py]

POST /authorizations  (merchant policy check)
  → PolicyEngine.evaluate()              [deterministic rule-based, policy_service.py]
      NO LLM involved
      MUTATION: authorizations INSERT (status=APPROVED/DENIED)

POST /checkout/orders  (create Razorpay order)
  → CheckoutService.create_checkout_order() [DB READ: authorization, quote]
      → RazorpayOrdersAdapter.create_order(amount=quote.total) [EXTERNAL API]
      MUTATION: orders INSERT

[Razorpay Checkout Modal in browser]

POST /payments/verify  (after customer pays)
  → HMAC-SHA256 verify: payments.py:59   [deterministic cryptographic gate]
      if invalid: raise ValidationError (no DB change)
  → order.status = "PAID"               [DB WRITE: orders UPDATE]
  → Payment INSERT                       [DB WRITE: payments INSERT]
  → cart.status = "COMPLETED"           [DB WRITE: carts UPDATE]
  → inv.available_quantity -= item.quantity  [DB WRITE: inventory UPDATE]
      if inv == 0: product.is_active = False [DB WRITE: products UPDATE]
  → AuditEvent INSERT (PAYMENT_CAPTURED) [DB WRITE: audit_events INSERT]
  MUTATION: 5 tables written atomically in one commit
```

---

## Merchant Simulation Flow

```
POST /optimization/simulations  (merchant runs simulation)
  → get_current_merchant()              [auth gate, authentication.py]
  → ProductService.get_active_catalogue() [DB READ: ALL active products, no LIMIT]
      SQL: SELECT products.* + inventory.available_quantity
           FROM products LEFT JOIN inventory
           WHERE merchant_id=:id AND is_active=TRUE
           ORDER BY products.id
      MUTATION: none
  → For each scenario in req.scenario_count:
      → _resolve_persona_weights()      [deterministic lookup, simulations.py:110]
      → SCENARIO_WEIGHT_OVERRIDES check [deterministic, simulations.py:70]
      → SimulationEngine.run_simulation() [100% deterministic, engine.py]
          → FrictionDetector.detect_hard_constraints() [deterministic, friction.py:23]
              Hard reject: PRICE_MISMATCH, INVENTORY_ISSUE, MISSING_FEATURE, DELIVERY_UNKNOWN, DELIVERY_TOO_SLOW
          → FrictionDetector.detect_soft_friction()    [deterministic, friction.py:77]
              Soft flags: DELIVERY_UNCLEAR, RETURN_UNCLEAR, INSUFFICIENT_PRODUCT_INFORMATION
          → ProductScorer.calculate_score()            [deterministic float64, scoring.py:15]
          → candidates.sort(key=(-score, str(product_id)))  [deterministic, engine.py:65]
          → selected = candidates[0]   [top-1 selection]
      → evaluations.append(result)     [in-memory accumulation]
  → Calculate summary_metrics          [deterministic formulas, simulations.py:310]
  → truncate_rankings(max_passed=20, max_disqualified=10, +winner) [payload bound]
  → SimulationRun INSERT               [DB WRITE: simulation_runs]
  → SimulationResult INSERT × N        [DB WRITE: simulation_results]
  → recommendation_service.generate_recommendations() [DB WRITE: optimization_recommendations UPSERT]
  MUTATION: 3 tables written

GET /optimization/recommendations
  → Fetch latest SimulationRun by created_at desc [DB READ]
  → List OptimizationRecommendation for latest run [DB READ]

PATCH /optimization/recommendations/{id}/status  (merchant applies)
  → if status == "APPLIED" and action_data exists:
      → Per affected product:
          price *= (1 - discount_pct/100)   [DB WRITE: products.price]
          metadata["delivery_days"] = N      [DB WRITE: products.product_metadata JSON]
          metadata["return_days"] = N        [DB WRITE: products.product_metadata JSON]
          inventory.available_quantity = 50  [DB WRITE: inventory.available_quantity]
      → AuditEvent INSERT (RECOMMENDATION_APPLIED) [DB WRITE: audit_events]
  → recommendation.status = "APPLIED"       [DB WRITE: optimization_recommendations]
  MUTATION: products, inventory, audit_events, optimization_recommendations

POST /optimization/what-if  (merchant tests hypothesis)
  → get_active_catalogue()             [DB READ, no LIMIT]
  → modified_catalogue = deepcopy()    [in-memory, NO DB READ for modifications]
  → Apply price/delivery/return overrides to in-memory copy
  → Run simulation on baseline + modified [100% deterministic, in-memory]
  → WhatIfRun INSERT                   [DB WRITE: what_if_runs (metrics only, NOT product mutations)]
  MUTATION: 1 table (metrics only)

POST /optimization/campaigns (LLM-assisted)
  → campaign_service.generate_campaign_proposals() [LLM called HERE]
      → llm_client.generate_text(prompt) [AI call, probabilistic]
      MUTATION: campaigns INSERT
```

---

## AI/Deterministic Boundaries

| Point | What LLM Produces | Deterministic Gate After | File |
|---|---|---|---|
| `IntentParser.parse()` | `StructuredIntent` JSON | `schema.model_validate(parsed_data)` — Pydantic validation; invalid = exception | `client.py:57` |
| `CampaignService` LLM call | Raw string (campaign text) | `len(message_content) >= 10` check only — no structural validation | `campaign_service.py:73` |
| **No other LLM calls** | — | — | — |
| Simulation ranking | — | 100% deterministic Python (no LLM) | `engine.py:65` |
| Payment amount | — | Read from `quote.total` (DB) only, LLM never touches | `checkout_service.py:78` |
