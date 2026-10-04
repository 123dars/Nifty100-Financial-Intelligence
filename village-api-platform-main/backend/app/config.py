from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    API_KEY_HEADER: str = "X-API-Key"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Authentication / JWT
    JWT_SECRET: str = "change-me-in-production-0123456789abcdef"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60 * 24  # 24 hours

    # Rate limiting
    RATE_LIMIT_WINDOW_SECONDS: int = 3600  # 1 hour rolling window
    RATE_LIMIT_DAILY_DEFAULT: int = 5000

    # Plan tier limits (daily requests / burst per minute)
    PLAN_LIMITS: dict = {
        "free": {"daily": 5000, "burst": 100},
        "premium": {"daily": 50000, "burst": 500},
        "pro": {"daily": 300000, "burst": 2000},
        "unlimited": {"daily": 1000000, "burst": 5000},
    }

    # SMTP / Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "noreply@villageapi.com"

    # Admin seed
    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    # Application URLs
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"

    # Daily request log budget used by the dashboard/admin stats
    LOG_LEVEL: str = "INFO"


settings = Settings()