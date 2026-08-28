from fastapi import APIRouter
from app.api.v1.optimization.simulations import router as simulations_router
from app.api.v1.optimization.recommendations import router as recommendations_router
from app.api.v1.optimization.what_if import router as what_if_router

optimization_router = APIRouter()
optimization_router.include_router(simulations_router)
optimization_router.include_router(recommendations_router)
optimization_router.include_router(what_if_router)

__all__ = ["optimization_router"]
