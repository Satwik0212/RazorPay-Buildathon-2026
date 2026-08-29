import uuid
from typing import List
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
from app.ai.intent_parser import intent_parser

router = APIRouter(tags=["Buyer"])


@router.post("/buyer/intents", response_model=BuyerIntentResponse, status_code=status.HTTP_200_OK)
def parse_buyer_intent(req: BuyerIntentRequest):
    """
    Synchronous intent parser interface.
    Extracts category, budget, requirements, and preferences from natural language.
    """
    parsed = intent_parser.parse(req.text)
    return BuyerIntentResponse(
        intent_id=uuid.uuid4(),
        intent=parsed,
    )


@router.post("/catalogue/search", response_model=CatalogueSearchResponse)
def search_catalogue(req: CatalogueSearchRequest, db: Session = Depends(get_db)):
    """
    Search and rank catalogue products based on buyer requirements and preferences.
    Grounded in real database products.
    """
    service = ProductService(db)
    # Fetch active products matching category and/or budget constraints
    products, _ = service.list_products(
        category=req.category,
        max_price=req.max_budget,
        is_active=True,
        limit=50,
    )

    if not products and req.category:
        # Resilient fallback: search across product name / corpus if exact category mismatch
        products, _ = service.list_products(
            search=req.category,
            max_price=req.max_budget,
            is_active=True,
            limit=50,
        )

    results: List[SearchResultItem] = []
    for p in products:
        matched_constraints = []
        failed_constraints = []
        score_components = []

        # 1. Category check
        if req.category:
            if req.category.lower() in p.category.lower() or p.category.lower() in req.category.lower():
                matched_constraints.append(f"category:{req.category}")
                score_components.append(0.30)
            else:
                failed_constraints.append(f"category_mismatch:{p.category}")
                score_components.append(0.0)
        else:
            score_components.append(0.30)

        # 2. Budget check
        if req.max_budget is not None:
            if p.price <= req.max_budget:
                matched_constraints.append("budget_compliant")
                budget_ratio = (req.max_budget - p.price) / max(req.max_budget, 1)
                score_components.append(0.20 + (0.10 * min(budget_ratio, 1.0)))
            else:
                failed_constraints.append("exceeds_budget")
                score_components.append(0.0)
        else:
            score_components.append(0.30)

        # 3. Requirements matching (metadata, name, description)
        p_metadata = p.product_metadata or {}
        p_text_corpus = f"{p.name} {p.description} {str(p_metadata)}".lower()

        if req.requirements:
            req_matched = 0
            for r in req.requirements:
                r_clean = r.lower().replace("_", " ")
                if r_clean in p_text_corpus or str(p_metadata.get(r.lower(), "")).lower() == "true":
                    matched_constraints.append(f"requirement:{r}")
                    req_matched += 1
                else:
                    failed_constraints.append(f"missing_requirement:{r}")
            req_score = 0.25 * (req_matched / len(req.requirements))
            score_components.append(req_score)
        else:
            score_components.append(0.25)

        # 4. Preferences matching
        if req.preferences:
            pref_matched = 0
            for pref in req.preferences:
                pref_clean = pref.lower().replace("_", " ")
                if pref_clean in p_text_corpus or str(p_metadata.get(pref.lower(), "")).lower() == "true":
                    matched_constraints.append(f"preference:{pref}")
                    pref_matched += 1
            pref_score = 0.15 * (pref_matched / len(req.preferences))
            score_components.append(pref_score)
        else:
            score_components.append(0.15)

        total_match_score = round(sum(score_components), 3)

        results.append(
            SearchResultItem(
                product_id=p.id,
                name=p.name,
                price=p.price,
                category=p.category,
                match_score=total_match_score,
                matched_constraints=matched_constraints,
                failed_constraints=failed_constraints,
            )
        )

    # Sort descending by match_score
    results.sort(key=lambda item: item.match_score, reverse=True)
    return CatalogueSearchResponse(results=results)
