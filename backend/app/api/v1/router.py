from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.products import router as products_router
from app.api.v1.catalog import router as catalog_router
from app.api.v1.carts import router as carts_router
from app.api.v1.quotes import router as quotes_router
from app.api.v1.policies import router as policies_router
from app.api.v1.authorizations import router as authorizations_router
from app.api.v1.checkout import router as checkout_router
from app.api.v1.payments import router as payments_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.audit import router as audit_router
from app.api.v1.buyer.intents import router as buyer_intents_router
from app.api.v1.buyer.personas import router as buyer_personas_router
from app.api.v1.optimization.simulations import router as simulations_router
from app.api.v1.optimization.recommendations import router as recommendations_router
from app.api.v1.optimization.what_if import router as what_if_router

api_v1_router = APIRouter()

# P0 Core Commerce & Auth
api_v1_router.include_router(auth_router)
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(products_router)
api_v1_router.include_router(catalog_router)
api_v1_router.include_router(carts_router)
api_v1_router.include_router(quotes_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(authorizations_router)
api_v1_router.include_router(checkout_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(webhooks_router)
api_v1_router.include_router(audit_router)

# Shared AI / Buyer / Simulation Boundaries (Sanji integration)
api_v1_router.include_router(buyer_intents_router)
api_v1_router.include_router(buyer_personas_router)
api_v1_router.include_router(simulations_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(what_if_router)

__all__ = ["api_v1_router"]
