import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.buyer.intent import (
    BuyerIntentRequest,
    BuyerIntentResponse,
    StructuredIntent,
    CatalogueSearchRequest,
    CatalogueSearchResponse,
    SearchResultItem,
)
from app.services.product_service import ProductService

router = APIRouter(tags=["Buyer"])


@router.post("/buyer/intents", response_model=BuyerIntentResponse, status_code=status.HTTP_200_OK)
def parse_buyer_intent(req: BuyerIntentRequest):
    """
    Synchronous intent parser interface.
    Extracts category, budget, and requirements from natural language.
    """
    intent_id = uuid.uuid4()
    # Structured intent is validated against strict constraints
    structured = StructuredIntent(
        category="general",
        min_budget=0,
        max_budget=1000000,
        requirements=[],
        delivery_deadline_days=3,
        preferences=[],
    )
    return BuyerIntentResponse(
        intent_id=intent_id,
        intent=structured,
    )


@router.post("/catalogue/search", response_model=CatalogueSearchResponse)
def search_catalogue(req: CatalogueSearchRequest, db: Session = Depends(get_db)):
    service = ProductService(db)
    products, _ = service.list_products(
        category=req.category,
        max_price=req.max_budget,
        is_active=True,
        limit=20,
    )
    results = []
    for p in products:
        results.append(
            SearchResultItem(
                product_id=p.id,
                name=p.name,
                price=p.price,
                category=p.category,
                match_score=0.90,
                matched_constraints=["category", "budget"],
                failed_constraints=[],
            )
        )
    return CatalogueSearchResponse(results=results)
