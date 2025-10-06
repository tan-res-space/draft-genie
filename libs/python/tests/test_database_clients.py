"""Tests for database clients."""

import pytest

from database.postgres import PostgresClient, init_postgres_client
from database.mongodb import MongoDBClient, init_mongodb_client
from database.qdrant import QdrantClientWrapper, init_qdrant_client
from database.redis import RedisClient, init_redis_client


class TestPostgresClient:
    """Tests for PostgresClient."""

    def test_create_postgres_client(self):
        """Test creating PostgreSQL client."""
        client = PostgresClient(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert client.host == "localhost"
        assert client.port == 5432
        assert client.database == "test_db"
        assert client.username == "test_user"

    def test_postgres_connection_string(self):
        """Test PostgreSQL connection string."""
        client = PostgresClient(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert "postgresql+asyncpg://" in client.connection_string
        assert "test_user:test_pass" in client.connection_string
        assert "localhost:5432" in client.connection_string
        assert "test_db" in client.connection_string

    def test_postgres_sync_connection_string(self):
        """Test PostgreSQL sync connection string."""
        client = PostgresClient(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert "postgresql://" in client.sync_connection_string
        assert "asyncpg" not in client.sync_connection_string

    def test_init_postgres_client(self):
        """Test initializing global PostgreSQL client."""
        client = init_postgres_client(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert isinstance(client, PostgresClient)


class TestMongoDBClient:
    """Tests for MongoDBClient."""

    def test_create_mongodb_client(self):
        """Test creating MongoDB client."""
        client = MongoDBClient(
            host="localhost",
            port=27017,
            database="test_db",
        )
        assert client.host == "localhost"
        assert client.port == 27017
        assert client.database_name == "test_db"

    def test_mongodb_connection_string_without_auth(self):
        """Test MongoDB connection string without authentication."""
        client = MongoDBClient(
            host="localhost",
            port=27017,
            database="test_db",
        )
        assert client.connection_string == "mongodb://localhost:27017/test_db"

    def test_mongodb_connection_string_with_auth(self):
        """Test MongoDB connection string with authentication."""
        client = MongoDBClient(
            host="localhost",
            port=27017,
            database="test_db",
            username="test_user",
            password="test_pass",
        )
        assert "test_user:test_pass" in client.connection_string
        assert "localhost:27017" in client.connection_string

    def test_init_mongodb_client(self):
        """Test initializing global MongoDB client."""
        client = init_mongodb_client(
            host="localhost",
            port=27017,
            database="test_db",
        )
        assert isinstance(client, MongoDBClient)


class TestQdrantClient:
    """Tests for QdrantClientWrapper."""

    def test_create_qdrant_client(self):
        """Test creating Qdrant client."""
        client = QdrantClientWrapper(
            host="localhost",
            port=6333,
        )
        assert client.host == "localhost"
        assert client.port == 6333

    def test_qdrant_client_with_api_key(self):
        """Test Qdrant client with API key."""
        client = QdrantClientWrapper(
            host="localhost",
            port=6333,
            api_key="test_key",
        )
        assert client.api_key == "test_key"

    def test_init_qdrant_client(self):
        """Test initializing global Qdrant client."""
        client = init_qdrant_client(
            host="localhost",
            port=6333,
        )
        assert isinstance(client, QdrantClientWrapper)


class TestRedisClient:
    """Tests for RedisClient."""

    def test_create_redis_client(self):
        """Test creating Redis client."""
        client = RedisClient(
            host="localhost",
            port=6379,
            db=0,
        )
        assert client.host == "localhost"
        assert client.port == 6379
        assert client.db == 0

    def test_redis_client_with_password(self):
        """Test Redis client with password."""
        client = RedisClient(
            host="localhost",
            port=6379,
            db=0,
            password="test_pass",
        )
        assert client.password == "test_pass"

    def test_init_redis_client(self):
        """Test initializing global Redis client."""
        client = init_redis_client(
            host="localhost",
            port=6379,
            db=0,
        )
        assert isinstance(client, RedisClient)


# Integration tests (require actual database connections)
# These are marked with pytest.mark.integration and can be skipped

@pytest.mark.integration
@pytest.mark.asyncio
async def test_postgres_connection():
    """Test PostgreSQL connection (integration test)."""
    client = PostgresClient(
        host="localhost",
        port=5432,
        database="draft_genie_test",
        username="postgres",
        password="postgres",
    )
    await client.connect()
    health = await client.health_check()
    assert health["healthy"] is True
    await client.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mongodb_connection():
    """Test MongoDB connection (integration test)."""
    client = MongoDBClient(
        host="localhost",
        port=27017,
        database="draft_genie_test",
    )
    await client.connect()
    health = await client.health_check()
    assert health["healthy"] is True
    await client.disconnect()


@pytest.mark.integration
def test_qdrant_connection():
    """Test Qdrant connection (integration test)."""
    client = QdrantClientWrapper(
        host="localhost",
        port=6333,
    )
    client.connect()
    health = client.health_check()
    assert health["healthy"] is True
    client.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection():
    """Test Redis connection (integration test)."""
    client = RedisClient(
        host="localhost",
        port=6379,
        db=0,
    )
    await client.connect()
    health = await client.health_check()
    assert health["healthy"] is True
    await client.disconnect()

