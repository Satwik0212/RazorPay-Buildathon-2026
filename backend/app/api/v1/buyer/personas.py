import uuid
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.buyer.persona import BuyerPersonaCreate, BuyerPersonaResponse
from app.models.buyer_persona import BuyerPersona

router = APIRouter(prefix="/buyer-personas", tags=["Buyer Personas"])


@router.get("", response_model=List[BuyerPersonaResponse])
def list_buyer_personas(db: Session = Depends(get_db)):
    """
    List all synthetic buyer personas from the database.
    """
    db_personas = db.query(BuyerPersona).all()
    return db_personas


@router.post("", response_model=BuyerPersonaResponse, status_code=status.HTTP_201_CREATED)
def create_buyer_persona(req: BuyerPersonaCreate, db: Session = Depends(get_db)):
    """
    Create a new custom buyer persona with validated scoring weights.
    """
    if req.weights:
        total_weight = sum(req.weights.values())
        if abs(total_weight - 1.0) > 0.001:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Persona weights must sum to 1.0, current sum is {total_weight:.3f}",
            )

    new_persona = BuyerPersona(
        name=req.name,
        description=req.description,
        budget_min=req.budget_min,
        budget_max=req.budget_max,
        priorities=req.priorities,
        urgency=req.urgency,
        weights=req.weights,
    )
    db.add(new_persona)
    try:
        db.commit()
        db.refresh(new_persona)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
        
    return new_persona
