"""Redis client for DraftGenie."""

import json
from typing import Any, Dict, List, Optional, Union

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, RedisError

from common.logger import LoggerMixin, get_logger

logger = get_logger(__name__)


class RedisClient(LoggerMixin):
    """Redis client with async support."""

    def __init__(
        self,
        host: str,
        port: int,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis client.

        Args:
            host: Redis host
            port: Redis port
            db: Database number
            password: Optional password
            max_connections: Maximum connections in pool
            decode_responses: Decode responses to strings
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.decode_responses = decode_responses

        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._client is not None:
            self.log_warning("Redis client already connected")
            return

        try:
            self._client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=self.decode_responses,
            )

            # Test connection
            await self._client.ping()

            self.log_info(
                "Connected to Redis",
                host=self.host,
                port=self.port,
                db=self.db,
            )
        except Exception as e:
            self.log_error("Failed to connect to Redis", error=e)
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._client is None:
            return

        try:
            await self._client.close()
            self._client = None
            self.log_info("Disconnected from Redis")
        except Exception as e:
            self.log_error("Failed to disconnect from Redis", error=e)
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            if self._client is None:
                return {"status": "disconnected", "healthy": False}

            await self._client.ping()

            info = await self._client.info()

            return {
                "status": "connected",
                "healthy": True,
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            self.log_error("Redis health check failed", error=e)
            return {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    @property
    def client(self) -> Redis:
        """Get the Redis client instance."""
        if self._client is None:
            raise RuntimeError("Redis client not connected")
        return self._client

    # Key-Value Operations

    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            return await self.client.get(key)
        except Exception as e:
            self.log_error("Failed to get key", error=e, key=key)
            raise

    async def set(
        self,
        key: str,
        value: str,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set key-value pair.

        Args:
            key: Key
            value: Value
            ex: Expiration in seconds
            px: Expiration in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if successful
        """
        try:
            result = await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
            return bool(result)
        except Exception as e:
            self.log_error("Failed to set key", error=e, key=key)
            raise

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        try:
            return await self.client.delete(*keys)
        except Exception as e:
            self.log_error("Failed to delete keys", error=e, keys=keys)
            raise

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        try:
            return await self.client.exists(*keys)
        except Exception as e:
            self.log_error("Failed to check key existence", error=e, keys=keys)
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            self.log_error("Failed to set expiration", error=e, key=key)
            raise

    async def ttl(self, key: str) -> int:
        """Get time to live for key."""
        try:
            return await self.client.ttl(key)
        except Exception as e:
            self.log_error("Failed to get TTL", error=e, key=key)
            raise

    # JSON Operations

    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key."""
        try:
            value = await self.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            self.log_error("Failed to get JSON", error=e, key=key)
            raise

    async def set_json(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
    ) -> bool:
        """Set JSON value."""
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ex=ex)
        except Exception as e:
            self.log_error("Failed to set JSON", error=e, key=key)
            raise

    # Hash Operations

    async def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        try:
            return await self.client.hget(name, key)
        except Exception as e:
            self.log_error("Failed to get hash field", error=e, name=name, key=key)
            raise

    async def hset(self, name: str, key: str, value: str) -> int:
        """Set hash field value."""
        try:
            return await self.client.hset(name, key, value)
        except Exception as e:
            self.log_error("Failed to set hash field", error=e, name=name, key=key)
            raise

    async def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields."""
        try:
            return await self.client.hgetall(name)
        except Exception as e:
            self.log_error("Failed to get all hash fields", error=e, name=name)
            raise

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        try:
            return await self.client.hdel(name, *keys)
        except Exception as e:
            self.log_error("Failed to delete hash fields", error=e, name=name, keys=keys)
            raise

    # List Operations

    async def lpush(self, name: str, *values: str) -> int:
        """Push values to list head."""
        try:
            return await self.client.lpush(name, *values)
        except Exception as e:
            self.log_error("Failed to push to list", error=e, name=name)
            raise

    async def rpush(self, name: str, *values: str) -> int:
        """Push values to list tail."""
        try:
            return await self.client.rpush(name, *values)
        except Exception as e:
            self.log_error("Failed to push to list", error=e, name=name)
            raise

    async def lrange(self, name: str, start: int, end: int) -> List[str]:
        """Get list range."""
        try:
            return await self.client.lrange(name, start, end)
        except Exception as e:
            self.log_error("Failed to get list range", error=e, name=name)
            raise

    # Cache Operations

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value (JSON)."""
        return await self.get_json(key)

    async def cache_set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set cached value (JSON) with TTL."""
        return await self.set_json(key, value, ex=ttl)

    async def cache_delete(self, key: str) -> int:
        """Delete cached value."""
        return await self.delete(key)


# Global client instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


def init_redis_client(
    host: str,
    port: int,
    db: int = 0,
    password: Optional[str] = None,
    **kwargs: Any,
) -> RedisClient:
    """Initialize the global Redis client."""
    global _redis_client
    _redis_client = RedisClient(
        host=host,
        port=port,
        db=db,
        password=password,
        **kwargs,
    )
    return _redis_client

