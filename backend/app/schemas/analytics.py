from pydantic import BaseModel, ConfigDict

class MerchantOverviewAnalytics(BaseModel):
    total_products: int
    active_products: int
    total_inventory: int
    total_categories: int
    total_personas: int
    total_recommendations: int
    
    model_config = ConfigDict(from_attributes=True)
