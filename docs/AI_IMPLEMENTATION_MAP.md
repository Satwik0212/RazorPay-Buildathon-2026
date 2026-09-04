# Document 1: AI_IMPLEMENTATION_MAP
> Ground truth on every AI call in this system. All claims verified against source code.

## 1. LLM Call Inventory

| # | File | Line | Function | Purpose | Provider | Deterministic? | Touches Financial State? |
|---|------|------|----------|---------|----------|----------------|--------------------------|
| 1 | `backend/app/ai/intent_parser.py` | 18 | `IntentParser.parse()` | NL → `StructuredIntent` | Groq→Sarvam→Offline | Probabilistic/Deterministic | NO |
| 2 | `backend/app/services/optimization/campaign_service.py` | 71 | `generate_campaign_proposals()` Strategy 1 | Campaign message from recommendation | Groq→Sarvam→Offline | Probabilistic | NO |
| 3 | `backend/app/services/optimization/campaign_service.py` | 125 | `generate_campaign_proposals()` Strategy 2 | Campaign message from friction | Groq→Sarvam→Offline | Probabilistic | NO |

**Total LLM calls: 3** (1 buyer flow, 2 merchant flow)

---

## 2. Per-Call Detail

### Call 1: Intent Parser (intent_parser.py:18)

**System Prompt (Groq):**
```text
You are a specialized buyer intent extraction engine.
You MUST output strictly valid JSON matching the following JSON schema:
{json.dumps(schema_json)}
Extract the user's intent. Do NOT add markdown formatting. Output raw JSON only.
```

**Input Schema:**
```python
class BuyerIntentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
```

**Output Schema:**
```python
class StructuredIntent(BaseModel):
    category: Optional[str] = Field(default=None, max_length=100)
    min_budget: Optional[int] = Field(default=None, ge=0)
    max_budget: Optional[int] = Field(default=None, ge=0)
    requirements: List[str] = Field(default_factory=list, max_length=20)
    delivery_deadline_days: Optional[int] = Field(default=None, ge=0, le=365)
    preferences: List[str] = Field(default_factory=list, max_length=20)
```

**Input Sanitization:**
```python
sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()
safe_prompt = f"<untrusted_buyer_text>\n{sanitized.strip()}\n</untrusted_buyer_text>"
```

**Output Validation:**
```python
parsed_data = json.loads(content)
return schema.model_validate(parsed_data)  # Pydantic raises ValidationError on violation
```

**Fallback chain:** Groq (10s) → Sarvam → OfflineProvider (pure regex, fully deterministic)

**Estimated tokens:** ~300 prompt + ~100 response

---

### Calls 2 & 3: Campaign Message (campaign_service.py:71, :125)

**System Prompt:** "You are an expert ecommerce marketing assistant."

**Strategy 1 User Prompt:**
```text
Generate a short, engaging campaign message for an ecommerce store.
The issue we are addressing is: {rec.title} ({rec.reason}).
The goal is to improve conversion rates for this segment.
Return ONLY the text of the message, nothing else.
```

**Output:** Unstructured plain text (string). Validated only by `len(message_content) >= 10`.

**Fallback:** Hardcoded template string if LLM fails or output < 10 chars.

**Financial/Inventory state affected? NO** — stored as `Campaign.message_content` (text only).

---

## 3. System Summary

| Category | Count | Notes |
|---|---|---|
| Total LLM calls | 3 | 1 buyer, 2 merchant campaign |
| Pydantic-validated output | 1 | Intent parsing only |
| Plain-text output | 2 | Campaign message generation |
| Affecting financial state | 0 | None |

---

## 4. Unused / Dead AI Code

- **`OfflineProvider.generate_text()`**: Always returns hardcoded string "Check out our latest offerings..." — never generates dynamic text. (`client.py:~277`)
- **`preferences` field in `StructuredIntent`**: Extracted by intent parser but **never passed to simulation engine**. Only `max_budget`, `requirements`, `delivery_deadline_days` are used in `simulations.py`.
- **`min_budget` field in `StructuredIntent`**: Extracted but there is **no lower-bound price filter** in simulation or search. Silently ignored.
- **Sarvam `generate_structured`**: Sarvam API returns plain text, not JSON. Implementation tries to parse it as JSON → always fails → cascades to Offline. Sarvam only works for `generate_text`. (`client.py:95-185`)
