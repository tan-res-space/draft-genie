"""PostgreSQL client for DraftGenie."""

from typing import Any, Dict, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from common.logger import LoggerMixin, get_logger

logger = get_logger(__name__)

Base = declarative_base()


class PostgresClient(LoggerMixin):
    """PostgreSQL client with async support."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
    ):
        """
        Initialize PostgreSQL client.

        Args:
            host: Database host
            port: Database port
            database: Database name
            username: Database username
            password: Database password
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            echo: Echo SQL statements
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo = echo

        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def connection_string(self) -> str:
        """Get async connection string."""
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def sync_connection_string(self) -> str:
        """Get sync connection string."""
        return (
            f"postgresql://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        if self._engine is not None:
            self.log_warning("PostgreSQL client already connected")
            return

        try:
            self._engine = create_async_engine(
                self.connection_string,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                echo=self.echo,
                pool_pre_ping=True,
            )

            self._session_factory = sessionmaker(
                self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Test connection
            async with self._engine.begin() as conn:
                await conn.execute(text("SELECT 1"))

            self.log_info(
                "Connected to PostgreSQL",
                host=self.host,
                port=self.port,
                database=self.database,
            )
        except Exception as e:
            self.log_error("Failed to connect to PostgreSQL", error=e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from PostgreSQL."""
        if self._engine is None:
            return

        try:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self.log_info("Disconnected from PostgreSQL")
        except Exception as e:
            self.log_error("Failed to disconnect from PostgreSQL", error=e)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL health."""
        try:
            if self._engine is None:
                return {"status": "disconnected", "healthy": False}

            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

            return {
                "status": "connected",
                "healthy": True,
                "host": self.host,
                "port": self.port,
                "database": self.database,
            }
        except Exception as e:
            self.log_error("PostgreSQL health check failed", error=e)
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if self._session_factory is None:
            raise RuntimeError("PostgreSQL client not connected")
        return self._session_factory()

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("PostgreSQL client not connected")
        return self._engine

    async def create_tables(self) -> None:
        """Create all tables."""
        if self._engine is None:
            raise RuntimeError("PostgreSQL client not connected")

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.log_info("Created PostgreSQL tables")
        except Exception as e:
            self.log_error("Failed to create PostgreSQL tables", error=e)
            raise

    async def drop_tables(self) -> None:
        """Drop all tables."""
        if self._engine is None:
            raise RuntimeError("PostgreSQL client not connected")

        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            self.log_info("Dropped PostgreSQL tables")
        except Exception as e:
            self.log_error("Failed to drop PostgreSQL tables", error=e)
            raise


# Global client instance
_postgres_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    """Get the global PostgreSQL client instance."""
    global _postgres_client
    if _postgres_client is None:
        raise RuntimeError("PostgreSQL client not initialized")
    return _postgres_client


def init_postgres_client(
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    **kwargs: Any,
) -> PostgresClient:
    """Initialize the global PostgreSQL client."""
    global _postgres_client
    _postgres_client = PostgresClient(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password,
        **kwargs,
    )
    return _postgres_client

