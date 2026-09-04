# Document 7: TEST_EVIDENCE
> Tests are proof. Summary from actual test files.

---

## A. Test File Inventory

| File | Lines | Tests | Category |
|---|---|---|---|
| `integration/test_analytics.py` | 46 | 1 | Analytics |
| `integration/test_auth.py` | 47 | 1 | Auth |
| `integration/test_campaigns.py` | 237 | 9 | Campaigns |
| `integration/test_cart.py` | 350 | 7 | Cart |
| `integration/test_catalogue.py` | 139 | 3 | Catalogue |
| `integration/test_catalogue_simulation.py` | 79 | 1 | Simulation |
| `integration/test_checkout.py` | 129 | 1 | Checkout |
| `integration/test_e2e_optimization_loop.py` | 159 | 1 | E2E |
| `integration/test_flipkart_importer.py` | 37 | 2 | Import |
| `integration/test_gate5_gate6_adversarial_verification.py` | 509 | 8 | Security |
| `integration/test_inventory_pipeline.py` | 263 | 11 | Inventory |
| `integration/test_optimization.py` | 432 | 5 | Optimization |
| `integration/test_simulation_variants_api.py` | 69 | 2 | Simulation |
| `integration/test_upsell.py` | 128 | 2 | Upsell |
| `payment/test_duplicate_webhook.py` | 118 | 1 | Payment |
| `payment/test_gate4_empirical_qa.py` | 617 | 9 | Payment QA |
| `payment/test_order_idempotency.py` | 3 | 0 | (placeholder) |
| `payment/test_payment_state.py` | 167 | 2 | Payment state |
| `payment/test_webhook_signature.py` | 36 | 1 | Payment security |
| `security/test_amount_tampering.py` | 73 | 1 | Security |
| `security/test_audit_security.py` | 9 | 1 | Audit |
| `security/test_authentication.py` | 35 | 6 | Auth |
| `security/test_authorization.py` | 27 | 3 | Auth |
| `security/test_idempotency.py` | 101 | 1 | Idempotency |
| `security/test_inventory_safety.py` | 163 | 1 | Inventory |
| `security/test_llm_output_validation.py` | 15 | 1 | AI |
| `security/test_ownership.py` | 137 | 2 | Auth |
| `security/test_prompt_injection.py` | 20 | 1 | AI safety |
| `security/test_secret_exposure.py` | 20 | 2 | Security |
| `unit/test_active_catalogue_retrieval.py` | 279 | 6 | Catalogue |
| `unit/test_ai.py` | 41 | 2 | AI |
| `unit/test_ai_providers.py` | 157 | 8 | AI |
| `unit/test_controlled_catalogue.py` | 211 | 15 | Simulation |
| `unit/test_custom_simulation.py` | 312 | 19 | Simulation |
| `unit/test_friction.py` | 92 | 7 | Friction |
| `unit/test_full_catalogue_simulation.py` | 382 | 5 | Simulation |
| `unit/test_metadata_normalization.py` | 158 | 18 | Normalization |
| `unit/test_optimization_api.py` | 112 | 3 | Optimization |
| `unit/test_policy_engine.py` | 76 | 1 | Policy |
| `unit/test_quote_service.py` | 112 | 2 | Quote |
| `unit/test_recommendation_service.py` | 102 | 2 | Recommendations |
| `unit/test_scoring.py` | 161 | 5 | Scoring |
| `unit/test_simulation.py` | 118 | 6 | Simulation |
| `unit/test_simulation_engine.py` | 242 | 5 | Simulation |
| `unit/test_simulation_variants.py` | 236 | 20 | Variants |
| `unit/test_step3_stress_challenge.py` | 695 | 12 | Stress |

**Total: 194 tests, 0 failures (as of latest run)**

---

## B. AI Test Details

```python
# unit/test_ai.py
def test_intent_parsing_distinct_queries()     # asserts different NL inputs → different StructuredIntent outputs
def test_prompt_injection_safety_formatting()  # asserts injection attempt is wrapped in boundary tags

# unit/test_ai_providers.py
def test_missing_keys_uses_offline(monkeypatch)         # assert empty API keys → OfflineProvider used
def test_groq_success(mock_post, monkeypatch)            # assert Groq happy path returns StructuredIntent
def test_groq_failure_sarvam_success(mock_post, ...)    # assert fallback to Sarvam on Groq 500
def test_groq_sarvam_failure_offline_fallback(...)      # assert final offline fallback works
def test_groq_malformed_output(mock_post, ...)          # assert malformed JSON → offline fallback
def test_sarvam_malformed_output(mock_post, ...)        # assert malformed Sarvam → offline
def test_prompt_injection_remains_contained(...)        # assert injected instructions do not leak into schema
def test_structured_intent_validation_enforced(...)     # assert Pydantic rejects invalid LLM output

# security/test_prompt_injection.py
def test_prompt_injection_in_buyer_intent()  # assert prompt injection does not affect parsed intent

# security/test_llm_output_validation.py
def test_llm_output_validation()  # assert LLM output is validated before use
```

**Mocked services:** Only `test_ai_providers.py` uses `monkeypatch` / `mock_post` to mock Groq/Sarvam HTTP calls. All other tests call real code paths.

---

## C. Payment Test Details

```python
# payment/test_payment_state.py
def test_payment_failure_state_machine(db_session)          # asserts PAID→FAILED is invalid transition
def test_illegal_state_transition_paid_to_failed(db_session) # asserts 400 on illegal transition

# payment/test_webhook_signature.py
def test_webhook_signature_verification()  # asserts invalid HMAC returns 400

# payment/test_duplicate_webhook.py
def test_webhook_event_idempotency_and_replay_protection()  # asserts second identical webhook is safe

# security/test_amount_tampering.py
def test_amount_tampering_prevention()   # asserts quote total cannot be tampered at checkout

# security/test_idempotency.py
def test_order_creation_idempotency()    # asserts same authorization_id → same order returned
```

---

## D. Simulation Test Details

```python
# unit/test_simulation_engine.py
def test_simulation_engine_ranked_selection()                      # winner = highest score
def test_simulation_engine_all_rejected_when_hard_constraints_fail() # all PRICE_MISMATCH → no winner
def test_equal_scores_deterministic_tie_breaking_by_product_id()   # same score → UUID sort decides
def test_ranking_permutation_invariance_100_runs()                 # 100 random shuffles → same result
def test_genuine_higher_score_ranks_above_lower_regardless_of_id() # score dominates UUID sort

# unit/test_scoring.py
def test_scoring_bounded_and_reproducible()
def test_scoring_missing_attributes_handled_safely()
def test_calculate_score_preserves_unquantized_precision()  # no float rounding at scorer level
def test_calculate_score_bounds_strict_enforcement()        # result always in [0.0, 1.0]
```

---

## E. Coverage Gaps

**Well-tested:**
- Simulation engine (determinism, tie-breaking, permutation invariance)
- AI provider fallback chain
- Payment signature verification, idempotency
- Metadata normalization (18 unit tests)
- Friction detection (7 unit tests)
- Custom simulation (19 unit tests)

**Zero or thin tests:**
- `GET/POST /buyer-personas` (no auth, no test for unauthorized access)
- Campaign service LLM integration (no test for campaign message quality or injection via friction text)
- Analytics endpoints (1 integration test, no formula verification)
- `reserved_quantity` in Inventory (field exists, never tested)
- What-If `modifications.metadata` deep override (partial coverage)
- `min_budget` / `preferences` from intent (not passed to simulation — no test documenting the gap)
- `test_order_idempotency.py` file is 3 lines long (empty placeholder)
