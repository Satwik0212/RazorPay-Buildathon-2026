from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class CatalogueCompletenessResponse(BaseModel):
    total_products: int
    complete_products: int
    needs_attention: int
    average_score: int

class MerchantOverviewAnalytics(BaseModel):
    total_products: int
    active_products: int
    total_inventory: int
    total_categories: int
    total_personas: int
    total_recommendations: int
    
    model_config = ConfigDict(from_attributes=True)

class PersonaPerformance(BaseModel):
    persona_name: str
    total_simulations: int
    matches: int
    rejections: int
    average_score: float
    top_frictions: List[str]

class FrictionBreakdown(BaseModel):
    friction_type: str
    count: int

class ProductIntelligence(BaseModel):
    product_id: str
    product_name: str
    problem: str
    evidence: str
    recommended_action: str
    recommendation_id: str

class RecommendationLifecycle(BaseModel):
    proposed: int
    applied: int
    rejected: int

class MerchantIntelligenceAnalytics(BaseModel):
    overview: MerchantOverviewAnalytics
    persona_performance: List[PersonaPerformance]
    friction_breakdown: List[FrictionBreakdown]
    product_intelligence: List[ProductIntelligence]
    recommendation_lifecycle: RecommendationLifecycle
