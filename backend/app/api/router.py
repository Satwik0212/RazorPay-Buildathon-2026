from fastapi import APIRouter
from app.api.v1.router import api_v1_router

main_api_router = APIRouter()
main_api_router.include_router(api_v1_router, prefix="/api/v1")

__all__ = ["main_api_router"]
