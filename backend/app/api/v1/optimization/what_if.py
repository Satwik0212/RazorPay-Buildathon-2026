import uuid
from datetime import datetime, timezone
from fastapi import APIRouter
from app.schemas.optimization.what_if import WhatIfRequest, WhatIfResponse

router = APIRouter(prefix="/optimization", tags=["Optimization"])


@router.post("/what-if", response_model=WhatIfResponse)
def run_what_if_analysis(req: WhatIfRequest):
    return WhatIfResponse(
        id=uuid.uuid4(),
        merchant_id=req.merchant_id,
        hypothesis=req.hypothesis,
        modifications=req.modifications,
        baseline_metrics={"conversion_rate": 0.15, "average_order_value": 49900},
        simulated_metrics={"conversion_rate": 0.18, "average_order_value": 49900},
        delta_percentage=20.0,
        created_at=datetime.now(timezone.utc),
    )
