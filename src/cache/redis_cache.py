"""
Redis Cache Implementation.

High-performance caching with Redis, featuring:
- Connection pooling
- Automatic serialization
- TTL management
- Cache invalidation patterns
- Distributed locking
"""

import asyncio
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    url: Optional[str] = None

    # Connection pool
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0

    # Default TTL
    default_ttl: int = 3600  # 1 hour

    # Serialization
    use_pickle: bool = False  # JSON by default, pickle for complex objects

    # Key prefix
    key_prefix: str = "flyready:"

    # Retry settings
    retry_on_timeout: bool = True
    max_retries: int = 3


class RedisCache:
    """
    Enterprise Redis cache manager.

    Features:
    - Async/await support
    - Connection pooling
    - Automatic reconnection
    - Multiple serialization formats
    - Pattern-based invalidation
    - Distributed locking
    """

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._connected:
            return

        async with self._lock:
            if self._connected:
                return

            try:
                if self.config.url:
                    self._pool = ConnectionPool.from_url(
                        self.config.url,
                        max_connections=self.config.max_connections,
                        socket_timeout=self.config.socket_timeout,
                        socket_connect_timeout=self.config.socket_connect_timeout,
                        retry_on_timeout=self.config.retry_on_timeout,
                    )
                else:
                    self._pool = ConnectionPool(
                        host=self.config.host,
                        port=self.config.port,
                        db=self.config.db,
                        password=self.config.password,
                        max_connections=self.config.max_connections,
                        socket_timeout=self.config.socket_timeout,
                        socket_connect_timeout=self.config.socket_connect_timeout,
                        retry_on_timeout=self.config.retry_on_timeout,
                    )

                self._client = Redis(connection_pool=self._pool)

                # Test connection
                await self._client.ping()
                self._connected = True
                logger.info("Redis cache connected successfully")

            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._connected = False
                raise

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._connected = False
        logger.info("Redis cache disconnected")

    def _make_key(self, key: str) -> str:
        """Generate full cache key with prefix."""
        return f"{self.config.key_prefix}{key}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self.config.use_pickle:
            return pickle.dumps(value)
        return json.dumps(value, default=str).encode()

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize stored value."""
        if not data:
            return None
        if self.config.use_pickle:
            return pickle.loads(data)
        return json.loads(data.decode())

    # =========================================================================
    # Basic Operations
    # =========================================================================

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            data = await self._client.get(full_key)

            if data is None:
                return default

            return self._deserialize(data)

        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False,
        xx: bool = False
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if set successfully
        """
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            data = self._serialize(value)
            ttl = ttl or self.config.default_ttl

            result = await self._client.set(
                full_key,
                data,
                ex=ttl,
                nx=nx,
                xx=xx
            )

            return bool(result)

        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            result = await self._client.delete(full_key)
            return result > 0
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.exists(full_key) > 0
        except Exception as e:
            logger.warning(f"Cache exists error for {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.expire(full_key, ttl)
        except Exception as e:
            logger.warning(f"Cache expire error for {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.ttl(full_key)
        except Exception as e:
            logger.warning(f"Cache ttl error for {key}: {e}")
            return -1

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once."""
        if not self._connected:
            await self.connect()

        try:
            full_keys = [self._make_key(k) for k in keys]
            values = await self._client.mget(full_keys)

            return {
                key: self._deserialize(val) if val else None
                for key, val in zip(keys, values)
            }
        except Exception as e:
            logger.warning(f"Cache mget error: {e}")
            return {}

    async def mset(
        self,
        mapping: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Set multiple keys at once."""
        if not self._connected:
            await self.connect()

        try:
            full_mapping = {
                self._make_key(k): self._serialize(v)
                for k, v in mapping.items()
            }

            async with self._client.pipeline() as pipe:
                await pipe.mset(full_mapping)

                if ttl:
                    for key in full_mapping.keys():
                        await pipe.expire(key, ttl)

                await pipe.execute()

            return True
        except Exception as e:
            logger.warning(f"Cache mset error: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._connected:
            await self.connect()

        try:
            full_pattern = self._make_key(pattern)
            keys = []

            async for key in self._client.scan_iter(match=full_pattern):
                keys.append(key)

            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete_pattern error: {e}")
            return 0

    # =========================================================================
    # Counter Operations
    # =========================================================================

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.incrby(full_key, amount)
        except Exception as e:
            logger.warning(f"Cache incr error: {e}")
            return 0

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement counter."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.decrby(full_key, amount)
        except Exception as e:
            logger.warning(f"Cache decr error: {e}")
            return 0

    # =========================================================================
    # Hash Operations
    # =========================================================================

    async def hget(self, name: str, key: str) -> Any:
        """Get hash field value."""
        if not self._connected:
            await self.connect()

        try:
            full_name = self._make_key(name)
            data = await self._client.hget(full_name, key)
            return self._deserialize(data) if data else None
        except Exception as e:
            logger.warning(f"Cache hget error: {e}")
            return None

    async def hset(self, name: str, key: str, value: Any) -> bool:
        """Set hash field value."""
        if not self._connected:
            await self.connect()

        try:
            full_name = self._make_key(name)
            data = self._serialize(value)
            await self._client.hset(full_name, key, data)
            return True
        except Exception as e:
            logger.warning(f"Cache hset error: {e}")
            return False

    async def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields."""
        if not self._connected:
            await self.connect()

        try:
            full_name = self._make_key(name)
            data = await self._client.hgetall(full_name)
            return {
                k.decode(): self._deserialize(v)
                for k, v in data.items()
            }
        except Exception as e:
            logger.warning(f"Cache hgetall error: {e}")
            return {}

    async def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields."""
        if not self._connected:
            await self.connect()

        try:
            full_name = self._make_key(name)
            return await self._client.hdel(full_name, *keys)
        except Exception as e:
            logger.warning(f"Cache hdel error: {e}")
            return 0

    # =========================================================================
    # List Operations
    # =========================================================================

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to left of list."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            serialized = [self._serialize(v) for v in values]
            return await self._client.lpush(full_key, *serialized)
        except Exception as e:
            logger.warning(f"Cache lpush error: {e}")
            return 0

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to right of list."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            serialized = [self._serialize(v) for v in values]
            return await self._client.rpush(full_key, *serialized)
        except Exception as e:
            logger.warning(f"Cache rpush error: {e}")
            return 0

    async def lrange(self, key: str, start: int, end: int) -> List[Any]:
        """Get list range."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            data = await self._client.lrange(full_key, start, end)
            return [self._deserialize(d) for d in data]
        except Exception as e:
            logger.warning(f"Cache lrange error: {e}")
            return []

    async def llen(self, key: str) -> int:
        """Get list length."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            return await self._client.llen(full_key)
        except Exception as e:
            logger.warning(f"Cache llen error: {e}")
            return 0

    # =========================================================================
    # Set Operations
    # =========================================================================

    async def sadd(self, key: str, *values: Any) -> int:
        """Add to set."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            serialized = [self._serialize(v) for v in values]
            return await self._client.sadd(full_key, *serialized)
        except Exception as e:
            logger.warning(f"Cache sadd error: {e}")
            return 0

    async def smembers(self, key: str) -> Set[Any]:
        """Get all set members."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            data = await self._client.smembers(full_key)
            return {self._deserialize(d) for d in data}
        except Exception as e:
            logger.warning(f"Cache smembers error: {e}")
            return set()

    async def sismember(self, key: str, value: Any) -> bool:
        """Check if value is in set."""
        if not self._connected:
            await self.connect()

        try:
            full_key = self._make_key(key)
            serialized = self._serialize(value)
            return await self._client.sismember(full_key, serialized)
        except Exception as e:
            logger.warning(f"Cache sismember error: {e}")
            return False

    # =========================================================================
    # Distributed Lock
    # =========================================================================

    async def acquire_lock(
        self,
        name: str,
        timeout: int = 10,
        blocking: bool = True,
        blocking_timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Acquire a distributed lock.

        Args:
            name: Lock name
            timeout: Lock timeout in seconds
            blocking: Whether to block waiting for lock
            blocking_timeout: Max time to wait for lock

        Returns:
            Lock token if acquired, None otherwise
        """
        if not self._connected:
            await self.connect()

        import uuid
        token = str(uuid.uuid4())
        lock_key = self._make_key(f"lock:{name}")

        end_time = None
        if blocking and blocking_timeout:
            end_time = asyncio.get_event_loop().time() + blocking_timeout

        while True:
            # Try to acquire lock
            acquired = await self._client.set(
                lock_key,
                token,
                ex=timeout,
                nx=True
            )

            if acquired:
                return token

            if not blocking:
                return None

            if end_time and asyncio.get_event_loop().time() >= end_time:
                return None

            await asyncio.sleep(0.1)

    async def release_lock(self, name: str, token: str) -> bool:
        """
        Release a distributed lock.

        Args:
            name: Lock name
            token: Lock token from acquire_lock

        Returns:
            True if lock was released
        """
        if not self._connected:
            await self.connect()

        lock_key = self._make_key(f"lock:{name}")

        # Lua script for atomic check and delete
        script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await self._client.eval(script, 1, lock_key, token)
            return bool(result)
        except Exception as e:
            logger.warning(f"Lock release error: {e}")
            return False

    # =========================================================================
    # Cache Stats
    # =========================================================================

    async def info(self) -> Dict[str, Any]:
        """Get Redis server info."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.info()
        except Exception as e:
            logger.warning(f"Cache info error: {e}")
            return {}

    async def dbsize(self) -> int:
        """Get number of keys in database."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.dbsize()
        except Exception as e:
            logger.warning(f"Cache dbsize error: {e}")
            return 0

    async def flush(self) -> bool:
        """Flush all keys (use with caution!)."""
        if not self._connected:
            await self.connect()

        try:
            await self._client.flushdb()
            return True
        except Exception as e:
            logger.warning(f"Cache flush error: {e}")
            return False


# Singleton instance
cache_manager = RedisCache()


# =========================================================================
# Decorator Functions
# =========================================================================

def cached(
    key_pattern: str,
    ttl: int = 3600,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Args:
        key_pattern: Cache key pattern (supports {arg_name} placeholders)
        ttl: Time-to-live in seconds
        key_builder: Custom function to build cache key

    Usage:
        @cached("user:{user_id}", ttl=300)
        async def get_user(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Simple key building from pattern
                cache_key = key_pattern.format(**kwargs)

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def cache_invalidate(key_pattern: str):
    """
    Decorator to invalidate cache after function execution.

    Args:
        key_pattern: Pattern of keys to invalidate

    Usage:
        @cache_invalidate("user:*")
        async def update_user(user_id: str, data: dict):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate cache
            if "*" in key_pattern:
                await cache_manager.delete_pattern(key_pattern)
            else:
                formatted_key = key_pattern.format(**kwargs)
                await cache_manager.delete(formatted_key)

            return result

        return wrapper
    return decorator
