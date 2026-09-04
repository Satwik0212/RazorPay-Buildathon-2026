# Document 8: EXPERIMENTAL_CODE
> Unused infrastructure, dead code, and incomplete features.

---

## A. Incomplete / Placeholder Code

| Item | File | Notes |
|---|---|---|
| `test_order_idempotency.py` | `backend/tests/payment/test_order_idempotency.py` | 3 lines total, no test functions. Empty placeholder. |
| `reserved_quantity` on Inventory | `backend/app/models/product.py:32` | Column defined (`Integer, default=0`). Never written by any service. Always 0. |
| `OfflineProvider.generate_text()` | `backend/app/integrations/llm/client.py:~277` | Returns hardcoded marketing string. Never personalized. |

---

## B. Disabled / Unused Services

| Item | File | Notes |
|---|---|---|
| `Sarvam generate_structured` path | `client.py:95-185` | Sarvam API returns plain text, not JSON. JSON parse always fails → cascades to offline. Sarvam only effective for `generate_text`. |
| `WhatIfService.compare()` | `what_if_service.py:14` | Single-persona direct comparison method. Not called by any API endpoint. Only `run_what_if()` is called. |

---

## C. Configuration Flags

| Flag | File | Current Value | Effect if Changed |
|---|---|---|---|
| `GROQ_API_KEY` | `backend/.env` / `config.py:30` | Required for Groq path | If blank, falls through to Sarvam/Offline |
| `SARVAM_API_KEY` | `config.py:32` | Optional | If blank, skips Sarvam |
| `LLM_PROVIDER` | `config.py:35` | Not used to control routing (routing is done by checking key presence, not this field) | Setting this has no effect on current code |
| `DEFAULT_QUOTE_EXPIRY_SECONDS` | `config.py` | Used by QuoteService | Controls quote TTL |

---

## D. Infrastructure Defined but Underused

| Item | File | Notes |
|---|---|---|
| `ProductRepository.decrement_inventory()` | `product_repository.py:132` | Atomic SQL UPDATE method using rowcount check. But the payment verify path (`payments.py:97`) does NOT use this — it manually reads and writes inventory inline. Two different inventory decrement patterns exist. |
| Search index on `products.name` | `models/product.py:14` | Index exists but search uses `ilike("%text%")` which cannot use a B-tree index. Effectively a full scan. |
| `buyer/upsell.py` endpoint | `backend/app/api/v1/buyer/upsell.py` | Fully implemented but the frontend does not appear to surface upsell recommendations in any visible UI flow per docs. |
