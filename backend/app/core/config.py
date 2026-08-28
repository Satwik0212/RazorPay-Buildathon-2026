from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Razorpay AI Buildathon Control Plane"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite:///./razorpay_buildathon.db"

    # Security & Auth
    JWT_SECRET: str = "buildathon-super-secret-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Razorpay (Test Mode)
    RAZORPAY_KEY_ID: str = "rzp_test_buildathon2026"
    RAZORPAY_KEY_SECRET: str = "test_buildathon_secret_key"
    RAZORPAY_WEBHOOK_SECRET: str = "test_buildathon_webhook_secret"

    # LLM (Sanji module)
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"

    # Business Defaults (Minor units, INR)
    DEFAULT_QUOTE_EXPIRY_SECONDS: int = 300  # 5 minutes
    DEFAULT_CURRENCY: str = "INR"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
