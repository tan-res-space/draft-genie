"""
Configuration management using Pydantic Settings
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
    app_name: str = Field(default="rag-service", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Log level")

    # API
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    host: str = Field(default="0.0.0.0", description="Host")
    port: int = Field(default_factory=lambda: get_port_from_config("rag-service", 3003), description="Port")

    # MongoDB
    mongodb_uri: str = Field(
        default="mongodb://draftgenie:draftgenie123@localhost:27017/draftgenie?authSource=admin", description="MongoDB URI"
    )
    mongodb_database: str = Field(
        default="draftgenie", description="MongoDB database name"
    )
    mongodb_min_pool_size: int = Field(default=10, description="MongoDB min pool size")
    mongodb_max_pool_size: int = Field(default=100, description="MongoDB max pool size")

    # Qdrant
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection_name: str = Field(
        default="correction_vectors", description="Qdrant collection name"
    )
    qdrant_vector_size: int = Field(default=768, description="Qdrant vector size")

    # RabbitMQ
    rabbitmq_host: str = Field(default="localhost", description="RabbitMQ host")
    rabbitmq_port: int = Field(default=5672, description="RabbitMQ port")
    rabbitmq_user: str = Field(default="draftgenie", description="RabbitMQ user")
    rabbitmq_password: str = Field(default="draftgenie123", description="RabbitMQ password")
    rabbitmq_vhost: str = Field(default="/", description="RabbitMQ vhost")
    rabbitmq_exchange: str = Field(
        default="draft_genie_events", description="RabbitMQ exchange"
    )
    rabbitmq_queue: str = Field(
        default="rag_service_queue", description="RabbitMQ queue"
    )

    # Gemini API
    gemini_api_key: str = Field(default="", description="Gemini API key")
    gemini_model: str = Field(default="models/gemini-pro", description="Gemini model")
    gemini_embedding_model: str = Field(
        default="models/embedding-001", description="Gemini embedding model"
    )
    gemini_embedding_dimension: int = Field(
        default=768, description="Gemini embedding dimension"
    )
    gemini_temperature: float = Field(default=0.7, description="Gemini temperature")
    gemini_max_tokens: int = Field(default=2048, description="Gemini max tokens")
    gemini_top_p: float = Field(default=0.95, description="Gemini top_p")
    gemini_top_k: int = Field(default=40, description="Gemini top_k")

    # External Services
    speaker_service_url: str = Field(
        default="http://localhost:8001", description="Speaker Service URL"
    )
    draft_service_url: str = Field(
        default="http://localhost:8002", description="Draft Service URL"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS origins",
    )
    cors_allow_credentials: bool = Field(
        default=True, description="CORS allow credentials"
    )
    cors_allow_methods: List[str] = Field(default=["*"], description="CORS allow methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="CORS allow headers")

    # API Documentation
    docs_url: str = Field(default="/docs", description="Swagger UI URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI schema URL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip("[]").split(",")]
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

