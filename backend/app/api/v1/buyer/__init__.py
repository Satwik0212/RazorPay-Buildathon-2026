from fastapi import APIRouter
from app.api.v1.buyer.intents import router as intents_router
from app.api.v1.buyer.personas import router as personas_router

buyer_router = APIRouter()
buyer_router.include_router(intents_router)
buyer_router.include_router(personas_router)

__all__ = ["buyer_router"]
