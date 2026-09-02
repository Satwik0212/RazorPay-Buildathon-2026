from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.database import Base, engine
from app.core.error_handlers import register_error_handlers
from app.api.router import main_api_router
import app.models  # Ensure all SQLAlchemy models are registered with Base metadata
from app.core.seed import seed_buyer_personas


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup logging and initialize tables if needed
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
    seed_buyer_personas()
    yield
    # Shutdown
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Deterministic Commerce and AI Governance Control Plane for Razorpay AI Buildathon 2026",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register uniform error handlers
register_error_handlers(app)

# Include main API routes (/api/v1/...)
app.include_router(main_api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main.py:app", host="0.0.0.0", port=8000, reload=True)
