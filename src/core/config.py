from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "ImpulseTech Backend API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    BACKEND_PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://impulsetech:impulsetech_secure_pass_2026@postgres:5432/impulsetech_dev"
    
    # Security / JWT
    JWT_SECRET_KEY: str = "impulsetech_super_secret_jwt_key_2026_dev_environment_at_least_32_bytes_long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:8000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
