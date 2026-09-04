"""
AI Upsell/Cross-sell Recommendation Reasoner.

Receives structured product context (already validated + filtered by UpsellService).
Sends deterministic candidate list to LLM for relevance reasoning.
Returns structured output validated by Pydantic — no hallucinated products/prices allowed.
"""
import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from app.integrations.llm.client import llm_client

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema: what the LLM must output — validated by Pydantic
# ---------------------------------------------------------------------------

class AiCandidateReasoning(BaseModel):
    """LLM output for a single candidate."""
    product_id: str = Field(description="Exact product_id from the candidate list — must not be invented.")
    recommendation_type: str = Field(description="Must be exactly 'UPSELL' or 'CROSS_SELL'.")
    reason: str = Field(description="One sentence grounded in actual product attributes. No invented specs.")
    confidence: float = Field(ge=0.0, le=1.0, description="Relevance confidence between 0 and 1.")


class AiUpsellOutput(BaseModel):
    """Top-level structured output from the LLM."""
    recommendations: List[AiCandidateReasoning] = Field(
        default_factory=list,
        description="Ranked recommendations, best first. May be empty if no good match."
    )


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------

def _product_summary(p: dict) -> str:
    """Build a compact, grounded product summary for the LLM prompt."""
    specs = p.get("specifications", {})
    spec_text = ", ".join(f"{k}: {v}" for k, v in list(specs.items())[:6]) if specs else "no specifications"
    price_inr = p.get("price", 0) / 100
    return (
        f'ID={p["id"]} | name="{p["name"]}" | category={p.get("category", "?")} | '
        f'price=₹{price_inr:.0f} | brand={p.get("brand", "?")} | {spec_text}'
    )


def _build_prompt(anchor_products: List[dict], upsell_candidates: List[dict], cross_sell_candidates: List[dict]) -> str:
    anchor_block = "\n".join(f"  - {_product_summary(a)}" for a in anchor_products)

    upsell_block = "\n".join(f"  - {_product_summary(c)}" for c in upsell_candidates[:10])
    cross_sell_block = "\n".join(f"  - {_product_summary(c)}" for c in cross_sell_candidates[:10])

    return f"""The buyer is viewing / has in cart:
{anchor_block}

UPSELL candidates (same category, higher price tier — pick the most relevant 1-3):
{upsell_block if upsell_candidates else "  (none)"}

CROSS-SELL candidates (different category — complementary to anchor — pick the most relevant 1-3):
{cross_sell_block if cross_sell_candidates else "  (none)"}

RULES:
- Only use product IDs from the lists above. Do NOT invent IDs.
- Do NOT invent prices, specs, brand claims, or compatibility assertions.
- Write reasons grounded only in the data you can see above.
- If you are unsure, use a lower confidence score (< 0.5).
- Return at most 3 upsell and 3 cross-sell recommendations total.
- Set recommendation_type to exactly "UPSELL" or "CROSS_SELL".
"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def get_ai_recommendations(
    anchor_products: List[dict],
    upsell_candidates: List[dict],
    cross_sell_candidates: List[dict],
) -> Optional[AiUpsellOutput]:
    """
    Call the LLM with structured candidate context.
    Returns None on any failure — the caller must handle gracefully.
    Never raises. Never blocks the purchase flow.
    """
    if not upsell_candidates and not cross_sell_candidates:
        return AiUpsellOutput(recommendations=[])

    prompt = _build_prompt(anchor_products, upsell_candidates, cross_sell_candidates)

    try:
        system_prompt = (
            "You are an AI product recommendation engine for an e-commerce platform. "
            "Your job is to select the most relevant upsell and cross-sell products "
            "from a provided candidate list. Be concise and grounded — only reference "
            "facts visible in the product data provided. Never invent product IDs, prices, "
            "specs, or claims not visible in the data."
        )
        result = llm_client.generate_structured(prompt, AiUpsellOutput, system_prompt)
        if result is None:
            logger.warning("ai_recommendation: LLM returned None, falling back to deterministic.")
            return None
        return result
    except Exception as e:
        logger.warning(f"ai_recommendation: exception during LLM call — {type(e).__name__}")
        return None
