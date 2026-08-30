from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Integer
from app.core.database import get_db
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant
from app.models.product import Product, Inventory
from app.models.optimization_recommendation import OptimizationRecommendation
from app.schemas.analytics import MerchantOverviewAnalytics
from app.api.v1.buyer.personas import DEFAULT_PERSONAS, _custom_personas

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=MerchantOverviewAnalytics)
def get_overview_analytics(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    """
    Retrieve real aggregated statistics for the merchant dashboard.
    """
    merchant_id = current_merchant.id

    # Aggregations for products
    product_stats = db.query(
        func.count(Product.id).label("total_products"),
        func.sum(cast(Product.is_active, Integer)).label("active_products"),
        func.count(distinct(Product.category)).label("total_categories")
    ).filter(Product.merchant_id == merchant_id).first()

    total_products = product_stats.total_products or 0
    active_products = product_stats.active_products or 0
    total_categories = product_stats.total_categories or 0

    # Total inventory
    total_inventory = db.query(func.sum(Inventory.available_quantity))\
        .join(Product)\
        .filter(Product.merchant_id == merchant_id).scalar() or 0

    # Total personas (Currently from memory as no DB model exists)
    total_personas = len(DEFAULT_PERSONAS) + len(_custom_personas)

    # Total recommendations from DB
    total_recommendations = db.query(func.count(OptimizationRecommendation.id))\
        .filter(OptimizationRecommendation.merchant_id == merchant_id).scalar() or 0

    return MerchantOverviewAnalytics(
        total_products=total_products,
        active_products=active_products,
        total_inventory=total_inventory,
        total_categories=total_categories,
        total_personas=total_personas,
        total_recommendations=total_recommendations
    )
