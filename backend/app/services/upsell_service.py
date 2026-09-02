import uuid
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.services.product_service import ProductService
from app.simulation.scoring import ProductScorer
from app.schemas.upsell.responses import UpsellSuggestion, UpsellResponse
from app.ai.intent_parser import intent_parser
from app.core.exceptions import NotFoundError, ForbiddenError


class UpsellService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)

    def get_cart_suggestions(self, cart_id: uuid.UUID, customer_id: uuid.UUID, context: Optional[str] = None, limit: int = 5) -> UpsellResponse:
        # Validate cart belongs to current customer
        cart = self.db.execute(select(Cart).where(Cart.id == cart_id)).scalar_one_or_none()
        if not cart:
            raise NotFoundError("Cart", cart_id)
        if cart.customer_id != customer_id:
            raise ForbiddenError("Cart belongs to another customer")
        
        # Get anchor products from cart items
        items = self.db.execute(select(CartItem).where(CartItem.cart_id == cart_id)).scalars().all()
        anchor_product_ids = [item.product_id for item in items]
        if not anchor_product_ids:
            return UpsellResponse(upsell=[], cross_sell=[], anchor_product_ids=[])

        anchor_products = []
        for pid in anchor_product_ids:
            anchor_products.append(self.product_service.get_product_by_id(pid))

        return self._generate_suggestions(anchor_products, cart.merchant_id, anchor_product_ids, context, limit)

    def get_product_suggestions(self, product_id: uuid.UUID, limit: int = 5) -> UpsellResponse:
        anchor_product = self.product_service.get_product_by_id(product_id)

        return self._generate_suggestions([anchor_product], anchor_product.merchant_id, [product_id], None, limit)

    def _generate_suggestions(self, anchor_products: List[Product], merchant_id: uuid.UUID, exclude_product_ids: List[uuid.UUID], context: Optional[str], limit: int) -> UpsellResponse:
        # Query catalogue for the merchant
        products, _ = self.product_service.list_products(merchant_id=merchant_id, is_active=True, limit=1000)
        
        # Filter available products
        available_products = []
        for p in products:
            if p.id in exclude_product_ids:
                continue
            if p.inventory and p.inventory.available_quantity > 0:
                available_products.append(p)
        
        if not available_products:
            return UpsellResponse(upsell=[], cross_sell=[], anchor_product_ids=exclude_product_ids)
            
        anchor_categories = {p.category for p in anchor_products if p.category}
        anchor_max_price = max((p.price for p in anchor_products), default=0)

        upsell_candidates = []
        cross_sell_candidates = []

        for p in available_products:
            if p.category in anchor_categories:
                # Upsell: same category, higher price or better tier (price >= anchor * 1.05)
                # We will just use price >= anchor_max_price for simplicity and rely on score to rank
                if p.price >= anchor_max_price:
                    upsell_candidates.append(p)
            else:
                cross_sell_candidates.append(p)

        # Score candidates
        # Use default balanced weights if no context provided or parsed intent has no direct weights
        weights = {"price": 0.33, "quality": 0.33, "delivery": 0.33, "metadata": 0.2}

        def score_product(p: Product) -> float:
            p_dict = {
                "price": p.price,
                "description": p.description,
                "metadata": p.product_metadata or {},
                "product_metadata": p.product_metadata or {}
            }
            return ProductScorer.calculate_score(p_dict, weights)

        # Score and sort
        scored_upsells = [(p, score_product(p)) for p in upsell_candidates]
        scored_upsells.sort(key=lambda x: x[1], reverse=True)

        scored_cross_sells = [(p, score_product(p)) for p in cross_sell_candidates]
        scored_cross_sells.sort(key=lambda x: x[1], reverse=True)

        # Build response
        def build_suggestion(p: Product, score: float) -> UpsellSuggestion:
            return UpsellSuggestion(
                product_id=p.id,
                name=p.name,
                price=p.price,
                category=p.category or "",
                score=score,
                explanation=None 
            )

        upsell_results = [build_suggestion(p, score) for p, score in scored_upsells[:limit]]
        cross_sell_results = [build_suggestion(p, score) for p, score in scored_cross_sells[:limit]]

        return UpsellResponse(
            upsell=upsell_results,
            cross_sell=cross_sell_results,
            anchor_product_ids=exclude_product_ids
        )
