import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.what_if import WhatIfRequest, WhatIfResponse
from app.services.product_service import ProductService
from app.services.optimization.what_if_service import what_if_service

router = APIRouter(prefix="/optimization", tags=["Optimization & What-If"])


@router.post("/what-if", response_model=WhatIfResponse, status_code=status.HTTP_200_OK)
def run_what_if_analysis(req: WhatIfRequest, db: Session = Depends(get_db)):
    """
    Executes a what-if catalogue optimization experiment in memory.
    Evaluates baseline catalogue vs proposed parameter changes without modifying database records.
    """
    product_service = ProductService(db)
    db_products, _ = product_service.list_products(merchant_id=req.merchant_id, limit=50)

    # Convert DB products to dictionary catalogue format
    catalogue: List[Dict[str, Any]] = []
    for p in db_products:
        inv_qty = p.inventory.available_quantity if hasattr(p, "inventory") and p.inventory else 10
        catalogue.append({
            "id": str(p.id),
            "name": p.name,
            "description": p.description or "",
            "category": p.category,
            "price": p.price,
            "currency": p.currency,
            "is_active": p.is_active,
            "product_metadata": p.product_metadata or {},
            "available_quantity": inv_qty,
        })

    # If no DB products exist yet for this merchant, create a baseline mock catalogue for testing
    if not catalogue:
        catalogue = [
            {
                "id": str(uuid.uuid4()),
                "name": "Standard Laptop Pro",
                "description": "Standard business laptop",
                "category": "laptop",
                "price": 549900,
                "currency": "INR",
                "is_active": True,
                "product_metadata": {"delivery_days": 5, "return_days": 7},
                "available_quantity": 20,
            }
        ]

    comparison = what_if_service.run_what_if(
        merchant_id=str(req.merchant_id),
        hypothesis=req.hypothesis,
        baseline_catalogue=catalogue,
        modifications=req.modifications,
    )

    return WhatIfResponse(
        id=uuid.uuid4(),
        merchant_id=req.merchant_id,
        hypothesis=req.hypothesis,
        modifications=req.modifications,
        baseline_metrics=comparison["baseline_metrics"],
        simulated_metrics=comparison["simulated_metrics"],
        delta_percentage=comparison["delta_percentage"],
        created_at=datetime.now(timezone.utc),
    )
