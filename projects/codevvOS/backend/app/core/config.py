from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        secrets_dir="/run/secrets",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Secrets — read from /run/secrets/<field_name> or env var fallback
    jwt_secret: str = Field(default="dev-jwt-secret-change-in-prod")
    postgres_password: str = Field(default="dev-postgres-password")
    anthropic_api_key: str = Field(default="")
    recall_api_key: str = Field(default="")
    bl_internal_secret: str = Field(default="dev-bl-secret")

    # Database connection params
    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="codevvos")
    postgres_user: str = Field(default="codevv_app")

    # Redis connection params
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"


settings = Settings()
