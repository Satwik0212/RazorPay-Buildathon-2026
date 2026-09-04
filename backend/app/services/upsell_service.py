import uuid
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.services.product_service import ProductService
from app.simulation.scoring import ProductScorer
from app.schemas.upsell.responses import UpsellSuggestion, UpsellResponse
from app.ai.recommendation import get_ai_recommendations
from app.core.exceptions import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)


class UpsellService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_cart_suggestions(
        self,
        cart_id: uuid.UUID,
        customer_id: uuid.UUID,
        context: Optional[str] = None,
        limit: int = 5,
    ) -> UpsellResponse:
        """Get upsell/cross-sell suggestions for a customer's active cart."""
        cart = self.db.execute(select(Cart).where(Cart.id == cart_id)).scalar_one_or_none()
        if not cart:
            raise NotFoundError("Cart", cart_id)
        if cart.customer_id != customer_id:
            raise ForbiddenError("Cart belongs to another customer")

        items = self.db.execute(select(CartItem).where(CartItem.cart_id == cart_id)).scalars().all()
        anchor_product_ids = [item.product_id for item in items]
        if not anchor_product_ids:
            return UpsellResponse(upsell=[], cross_sell=[], anchor_product_ids=[])

        anchor_products = [self.product_service.get_product_by_id(pid) for pid in anchor_product_ids]
        return self._generate_suggestions(anchor_products, cart.merchant_id, anchor_product_ids, limit)

    def get_product_suggestions(self, product_id: uuid.UUID, limit: int = 5) -> UpsellResponse:
        """Get upsell/cross-sell suggestions for a single product (product detail page)."""
        anchor_product = self.product_service.get_product_by_id(product_id)
        return self._generate_suggestions(
            [anchor_product], anchor_product.merchant_id, [product_id], limit
        )

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------

    def _generate_suggestions(
        self,
        anchor_products: List[Product],
        merchant_id: uuid.UUID,
        exclude_product_ids: List[uuid.UUID],
        limit: int,
    ) -> UpsellResponse:
        # 1. Deterministic candidate retrieval — same merchant, active, in-stock
        products, _ = self.product_service.list_products(
            merchant_id=merchant_id, is_active=True, limit=1000
        )

        available = [
            p for p in products
            if p.id not in exclude_product_ids
            and p.inventory
            and p.inventory.available_quantity > 0
        ]

        if not available:
            return UpsellResponse(upsell=[], cross_sell=[], anchor_product_ids=exclude_product_ids)

        anchor_categories = {p.category for p in anchor_products if p.category}
        anchor_max_price = max((p.price for p in anchor_products), default=0)

        # 2. Deterministic eligibility split
        upsell_candidates: List[Product] = []
        cross_sell_candidates: List[Product] = []

        for p in available:
            if p.category in anchor_categories:
                # Upsell: same category, at least 5 % more expensive
                if p.price >= anchor_max_price * 1.05:
                    upsell_candidates.append(p)
            else:
                cross_sell_candidates.append(p)

        # 3. Score + take top-N before sending to LLM (keeps prompt small)
        weights = {"price": 0.33, "quality": 0.33, "delivery": 0.33, "metadata": 0.2}

        def score(p: Product) -> float:
            return ProductScorer.calculate_score(
                {"price": p.price, "description": p.description,
                 "metadata": p.product_metadata or {},
                 "product_metadata": p.product_metadata or {}},
                weights,
            )

        scored_upsells = sorted([(p, score(p)) for p in upsell_candidates], key=lambda x: x[1], reverse=True)
        scored_cross = sorted([(p, score(p)) for p in cross_sell_candidates], key=lambda x: x[1], reverse=True)

        top_upsell = [p for p, _ in scored_upsells[:limit * 3]]
        top_cross = [p for p, _ in scored_cross[:limit * 3]]

        # 4. AI reasoning layer — builds explanations from actual attributes
        anchor_dicts = [self._product_to_dict(p) for p in anchor_products]
        upsell_dicts = [self._product_to_dict(p) for p in top_upsell]
        cross_dicts = [self._product_to_dict(p) for p in top_cross]

        ai_output = get_ai_recommendations(anchor_dicts, upsell_dicts, cross_dicts)

        # 5. Merge AI explanations into deterministic results (AI cannot alter order/price)
        ai_map: dict[str, dict] = {}
        ai_powered = False
        if ai_output and ai_output.recommendations:
            ai_powered = True
            for rec in ai_output.recommendations:
                ai_map[str(rec.product_id)] = {
                    "reason": rec.reason,
                    "confidence": rec.confidence,
                    "type": rec.recommendation_type,
                }

        # 6. Build validated suggestions (backend is authoritative on type/price/score)
        def build_suggestion(p: Product, det_score: float, rec_type: str) -> UpsellSuggestion:
            pid_str = str(p.id)
            ai_rec = ai_map.get(pid_str, {})
            # Only use AI explanation if the product ID was genuinely returned by AI
            explanation = ai_rec.get("reason") if ai_rec else None
            confidence = ai_rec.get("confidence") if ai_rec else None
            return UpsellSuggestion(
                product_id=p.id,
                name=p.name,
                price=p.price,
                category=p.category or "",
                score=det_score,
                explanation=explanation,
                recommendation_type=rec_type,
                ai_confidence=confidence,
            )

        # Deterministic ordering; AI only provides the explanation text
        upsell_results = [
            build_suggestion(p, s, "UPSELL") for p, s in scored_upsells[:limit]
        ]
        cross_results = [
            build_suggestion(p, s, "CROSS_SELL") for p, s in scored_cross[:limit]
        ]

        return UpsellResponse(
            upsell=upsell_results,
            cross_sell=cross_results,
            anchor_product_ids=exclude_product_ids,
            data_source="AI_GROUNDED_CATALOGUE" if ai_powered else "DETERMINISTIC_CATALOGUE_SCORING",
            ai_powered=ai_powered,
        )

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    @staticmethod
    def _product_to_dict(p: Product) -> dict:
        meta = p.product_metadata or {}
        return {
            "id": str(p.id),
            "name": p.name,
            "category": p.category or "",
            "price": p.price,
            "brand": meta.get("brand", ""),
            "specifications": meta.get("specifications", {}),
            "description": (p.description or "")[:300],
        }
