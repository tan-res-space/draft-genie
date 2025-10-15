"""
Application configuration using Pydantic Settings
"""
import json
import os
from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_port_from_config(service_name: str, default_port: int) -> int:
    """
    Read port from centralized config/ports.json file.
    Falls back to environment variable PORT, then to default_port.
    """
    # First check environment variable
    env_port = os.getenv("PORT")
    if env_port:
        return int(env_port)

    # Then check config file
    try:
        # Get project root - try multiple strategies
        config_path = None

        # Strategy 1: Use __file__ if available (4 levels up)
        if "__file__" in globals():
            file_path = Path(__file__).resolve()
            config_path = file_path.parent.parent.parent.parent / "config" / "ports.json"

        # Strategy 2: Search up from current directory
        if not config_path or not config_path.exists():
            current = Path.cwd()
            for _ in range(5):  # Search up to 5 levels
                test_path = current / "config" / "ports.json"
                if test_path.exists():
                    config_path = test_path
                    break
                current = current.parent

        if config_path and config_path.exists():
            with open(config_path, "r") as f:
                config = json.load(f)
                port = config.get("services", {}).get(service_name, {}).get("port")
                if port:
                    return int(port)
    except Exception:
        pass  # Fall back to default

    return default_port


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="draft-service", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    port: int = Field(default_factory=lambda: get_port_from_config("draft-service", 3002), alias="PORT")
    host: str = Field(default="0.0.0.0", alias="HOST")

    # MongoDB
    mongodb_url: str = Field(alias="MONGODB_URL")
    mongodb_database: str = Field(default="draftgenie", alias="MONGODB_DATABASE")
    mongodb_min_pool_size: int = Field(default=10, alias="MONGODB_MIN_POOL_SIZE")
    mongodb_max_pool_size: int = Field(default=100, alias="MONGODB_MAX_POOL_SIZE")

    # Qdrant
    qdrant_url: str = Field(alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection_name: str = Field(
        default="correction_vectors", alias="QDRANT_COLLECTION_NAME"
    )
    qdrant_vector_size: int = Field(default=768, alias="QDRANT_VECTOR_SIZE")

    # RabbitMQ
    rabbitmq_url: str = Field(alias="RABBITMQ_URL")
    rabbitmq_exchange: str = Field(default="draft-genie.events", alias="RABBITMQ_EXCHANGE")
    rabbitmq_queue: str = Field(default="draft.events", alias="RABBITMQ_QUEUE")
    rabbitmq_routing_key: str = Field(default="draft.*", alias="RABBITMQ_ROUTING_KEY")

    # Gemini API
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="models/embedding-001", alias="GEMINI_MODEL")
    gemini_embedding_dimension: int = Field(default=768, alias="GEMINI_EMBEDDING_DIMENSION")

    # InstaNote Mock API
    instanote_api_url: str = Field(alias="INSTANOTE_API_URL")
    instanote_api_key: str = Field(alias="INSTANOTE_API_KEY")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"], alias="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    # API Documentation
    docs_url: str = Field(default="/api/docs", alias="DOCS_URL")
    redoc_url: str = Field(default="/api/redoc", alias="REDOC_URL")
    openapi_url: str = Field(default="/api/openapi.json", alias="OPENAPI_URL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip("[]").replace('"', "").split(",")]
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()

