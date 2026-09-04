import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.optimization.what_if import WhatIfRequest, WhatIfResponse
from app.services.product_service import ProductService
from app.services.optimization.what_if_service import what_if_service

from app.core.exceptions import ValidationError
from app.security.authentication import get_current_merchant
from app.models.merchant import User
from app.models.buyer_persona import BuyerPersona
from app.models.what_if_run import WhatIfRun

router = APIRouter(prefix="/optimization", tags=["Optimization & What-If"])


@router.post("/what-if", response_model=WhatIfResponse, status_code=status.HTTP_200_OK)
def run_what_if_analysis(
    req: WhatIfRequest,
    db: Session = Depends(get_db),
    current_merchant: User = Depends(get_current_merchant)
):
    """
    Executes a what-if catalogue optimization experiment in memory.
    Evaluates baseline catalogue vs proposed parameter changes without modifying database records.
    """
    merchant_id = current_merchant.id
    product_service = ProductService(db)
    catalogue = product_service.get_active_catalogue(merchant_id=merchant_id)
    for p in catalogue:
        p["id"] = str(p["id"])

    if not catalogue:
        raise ValidationError("Merchant catalogue is empty. Cannot execute what-if analysis on an empty catalogue.")

    db_personas = db.query(BuyerPersona).all()
    if not db_personas:
        raise ValidationError("No buyer personas found in the database to run the what-if simulation.")

    comparison = what_if_service.run_what_if(
        merchant_id=str(merchant_id),
        hypothesis=req.hypothesis,
        baseline_catalogue=catalogue,
        modifications=req.modifications,
        db_personas=db_personas
    )

    run_id = uuid.uuid4()
    
    what_if_run = WhatIfRun(
        id=run_id,
        merchant_id=merchant_id,
        hypothesis=req.hypothesis,
        modifications=req.modifications,
        baseline_metrics=comparison["baseline_metrics"],
        simulated_metrics=comparison["simulated_metrics"],
        delta_percentage=comparison["delta_percentage"]
    )
    db.add(what_if_run)
    db.commit()

    return WhatIfResponse(
        id=run_id,
        merchant_id=merchant_id,
        hypothesis=req.hypothesis,
        modifications=req.modifications,
        baseline_metrics=comparison["baseline_metrics"],
        simulated_metrics=comparison["simulated_metrics"],
        delta_percentage=comparison["delta_percentage"],
        created_at=datetime.now(timezone.utc),
        target_product_metrics=comparison.get("target_product_metrics"),
    )

