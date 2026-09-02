from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, cast, Integer
from collections import defaultdict
from app.core.database import get_db
from app.security.authentication import get_current_merchant
from app.models.merchant import Merchant
from app.models.product import Product, Inventory
from app.models.optimization_recommendation import OptimizationRecommendation
from app.models.simulation_run import SimulationRun
from app.models.simulation_result import SimulationResult
from app.schemas.analytics import MerchantIntelligenceAnalytics, MerchantOverviewAnalytics, PersonaPerformance, FrictionBreakdown, ProductIntelligence, RecommendationLifecycle, CatalogueCompletenessResponse
from app.models.buyer_persona import BuyerPersona

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/overview", response_model=MerchantOverviewAnalytics)
def get_overview_analytics(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    merchant_id = current_merchant.id

    product_stats = db.query(
        func.count(Product.id).label("total_products"),
        func.sum(cast(Product.is_active, Integer)).label("active_products"),
        func.count(distinct(Product.category)).label("total_categories")
    ).filter(Product.merchant_id == merchant_id).first()

    total_products = product_stats.total_products or 0
    active_products = product_stats.active_products or 0
    total_categories = product_stats.total_categories or 0

    total_inventory = db.query(func.sum(Inventory.available_quantity))\
        .join(Product)\
        .filter(Product.merchant_id == merchant_id).scalar() or 0

    total_personas = db.query(func.count(BuyerPersona.id)).scalar() or 0

    total_recommendations = db.query(func.count(OptimizationRecommendation.id))\
        .filter(OptimizationRecommendation.merchant_id == merchant_id).scalar() or 0

    return MerchantOverviewAnalytics(
        total_products=total_products,
        active_products=active_products,
        total_inventory=total_inventory,
        total_categories=total_categories,
        total_personas=total_personas,
        total_recommendations=total_recommendations,
    )

@router.get("/catalogue-completeness", response_model=CatalogueCompletenessResponse)
def get_catalogue_completeness(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    products = db.query(Product).filter(Product.merchant_id == current_merchant.id).all()
    
    total_products = len(products)
    if total_products == 0:
        return CatalogueCompletenessResponse(
            total_products=0, complete_products=0, needs_attention=0, average_score=0
        )
        
    total_score = 0
    complete_count = 0
    
    for p in products:
        score = 0
        metadata = p.product_metadata or {}
        
        if p.description and len(p.description) > 50: score += 20
        if p.description and len(p.description) > 200: score += 10
        
        specs = metadata.get("specifications", {})
        spec_count = len(specs.keys()) if isinstance(specs, dict) else 0
        
        if spec_count > 0: score += 20
        if spec_count > 5: score += 10
        
        images = metadata.get("image_urls", [])
        if len(images) > 0: score += 20
        
        if metadata.get("brand"):
            score += 10
        elif spec_count > 0:
            score += 10
            
        if p.category and p.category != "Uncategorized":
            score += 10
            
        score = min(score, 100)
        total_score += score
        if score >= 70:
            complete_count += 1
            
    return CatalogueCompletenessResponse(
        total_products=total_products,
        complete_products=complete_count,
        needs_attention=total_products - complete_count,
        average_score=int(total_score / total_products)
    )

@router.get("/merchant-intelligence", response_model=MerchantIntelligenceAnalytics)

def get_merchant_intelligence(
    db: Session = Depends(get_db),
    current_merchant: Merchant = Depends(get_current_merchant)
):
    merchant_id = current_merchant.id

    # 1. Overview
    product_stats = db.query(
        func.count(Product.id).label("total_products"),
        func.sum(cast(Product.is_active, Integer)).label("active_products"),
        func.count(distinct(Product.category)).label("total_categories")
    ).filter(Product.merchant_id == merchant_id).first()

    total_products = product_stats.total_products or 0
    active_products = product_stats.active_products or 0
    total_categories = product_stats.total_categories or 0

    total_inventory = db.query(func.sum(Inventory.available_quantity))\
        .join(Product)\
        .filter(Product.merchant_id == merchant_id).scalar() or 0

    total_personas = db.query(func.count(BuyerPersona.id)).scalar() or 0

    total_recommendations = db.query(func.count(OptimizationRecommendation.id))\
        .filter(OptimizationRecommendation.merchant_id == merchant_id).scalar() or 0

    overview = MerchantOverviewAnalytics(
        total_products=total_products,
        active_products=active_products,
        total_inventory=total_inventory,
        total_categories=total_categories,
        total_personas=total_personas,
        total_recommendations=total_recommendations
    )

    # 2. Persona Performance and Friction Breakdown
    runs = db.query(SimulationRun).filter(SimulationRun.merchant_id == merchant_id).all()
    run_ids = [r.id for r in runs]
    
    persona_perf = {}
    friction_counts = defaultdict(int)
    
    if run_ids:
        results = db.query(SimulationResult).filter(SimulationResult.simulation_run_id.in_(run_ids)).all()
        for res in results:
            persona = res.persona_name
            if persona not in persona_perf:
                persona_perf[persona] = {
                    "total": 0, "matches": 0, "rejections": 0, "score_sum": 0.0, "frictions": defaultdict(int)
                }
            
            persona_perf[persona]["total"] += 1
            if res.constraints_satisfied:
                persona_perf[persona]["matches"] += 1
            else:
                persona_perf[persona]["rejections"] += 1
            persona_perf[persona]["score_sum"] += res.score
            
            for friction in res.frictions:
                f_type = friction.get("type", "unknown_friction")
                persona_perf[persona]["frictions"][f_type] += 1
                friction_counts[f_type] += 1
                
    persona_performance_list = []
    for p_name, data in persona_perf.items():
        total = data["total"]
        avg_score = data["score_sum"] / total if total > 0 else 0.0
        # sort frictions by count
        sorted_frictions = sorted(data["frictions"].items(), key=lambda x: x[1], reverse=True)
        top_frictions = [f[0] for f in sorted_frictions][:3]
        
        persona_performance_list.append(PersonaPerformance(
            persona_name=p_name,
            total_simulations=total,
            matches=data["matches"],
            rejections=data["rejections"],
            average_score=avg_score,
            top_frictions=top_frictions
        ))
        
    friction_breakdown_list = [
        FrictionBreakdown(friction_type=k, count=v) for k, v in sorted(friction_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # 3. Product Intelligence
    recommendations = db.query(OptimizationRecommendation, Product)\
        .outerjoin(Product, OptimizationRecommendation.product_id == Product.id)\
        .filter(OptimizationRecommendation.merchant_id == merchant_id)\
        .order_by(OptimizationRecommendation.created_at.desc())\
        .limit(20).all()
        
    product_intel_list = []
    proposed_count = 0
    applied_count = 0
    rejected_count = 0
    
    # Get all recommendations for lifecycle counts
    all_recs = db.query(OptimizationRecommendation.status, func.count(OptimizationRecommendation.id))\
        .filter(OptimizationRecommendation.merchant_id == merchant_id)\
        .group_by(OptimizationRecommendation.status).all()
        
    for r_status, count in all_recs:
        if r_status == "PROPOSED":
            proposed_count = count
        elif r_status == "APPLIED":
            applied_count = count
        elif r_status == "REJECTED":
            rejected_count = count
            
    for rec, prod in recommendations:
        product_intel_list.append(ProductIntelligence(
            product_id=str(prod.id) if prod else "",
            product_name=prod.name if prod else "Store-wide Recommendation",
            problem=rec.title,
            evidence=rec.reason,
            recommended_action=f"Apply {rec.type} recommendation",
            recommendation_id=str(rec.id)
        ))

    rec_lifecycle = RecommendationLifecycle(
        proposed=proposed_count,
        applied=applied_count,
        rejected=rejected_count
    )

    return MerchantIntelligenceAnalytics(
        overview=overview,
        persona_performance=persona_performance_list,
        friction_breakdown=friction_breakdown_list,
        product_intelligence=product_intel_list,
        recommendation_lifecycle=rec_lifecycle
    )
