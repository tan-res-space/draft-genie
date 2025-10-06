"""
Configuration settings for Evaluation Service
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    app_name: str = "evaluation-service"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8004
    log_level: str = "INFO"

    # API Documentation
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "evaluation_db"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    @property
    def database_url(self) -> str:
        """Get PostgreSQL database URL"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_exchange: str = "draft_genie"
    rabbitmq_exchange_type: str = "topic"

    @property
    def rabbitmq_url(self) -> str:
        """Get RabbitMQ connection URL"""
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}/{self.rabbitmq_vhost}"
        )

    # External Services
    speaker_service_url: str = "http://localhost:8001"
    draft_service_url: str = "http://localhost:8002"
    rag_service_url: str = "http://localhost:8003"

    # Evaluation Settings
    similarity_threshold: float = 0.7  # Threshold for semantic similarity
    quality_threshold: float = 0.8  # Threshold for quality score
    improvement_threshold: float = 0.15  # Threshold for improvement score

    # Sentence Transformer Model
    sentence_transformer_model: str = "all-MiniLM-L6-v2"  # Fast and efficient model

    # Bucket Reassignment Thresholds
    bucket_a_quality_threshold: float = 0.9  # High quality
    bucket_b_quality_threshold: float = 0.7  # Medium quality
    bucket_c_quality_threshold: float = 0.5  # Low quality

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()

