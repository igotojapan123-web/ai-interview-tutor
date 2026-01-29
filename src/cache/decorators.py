"""
Cache Decorators.

Advanced caching decorators for various use cases.
"""

import asyncio
import functools
import hashlib
import logging
from typing import Any, Callable, Optional, Type, Union

from src.cache.redis_cache import cache_manager
from src.cache.cache_keys import CacheKeys

logger = logging.getLogger(__name__)


def cache_response(
    ttl: int = CacheKeys.TTL_DEFAULT,
    key_prefix: str = "response",
    include_user: bool = False,
    vary_on: Optional[list] = None
):
    """
    Cache API response decorator.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Cache key prefix
        include_user: Include user_id in cache key
        vary_on: List of parameter names to vary cache on

    Usage:
        @cache_response(ttl=300, vary_on=["page", "limit"])
        async def list_items(page: int = 1, limit: int = 10):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix, func.__name__]

            # Add user ID if required
            if include_user:
                user_id = kwargs.get("user_id") or kwargs.get("current_user", {}).get("id")
                if user_id:
                    key_parts.append(f"user:{user_id}")

            # Add vary_on parameters
            if vary_on:
                for param in vary_on:
                    value = kwargs.get(param)
                    if value is not None:
                        key_parts.append(f"{param}:{value}")

            cache_key = ":".join(key_parts)

            # Try cache
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache_manager.set(cache_key, result, ttl=ttl)
            logger.debug(f"Cache set: {cache_key}")

            return result

        return wrapper
    return decorator


def cache_query(
    ttl: int = CacheKeys.TTL_MEDIUM,
    key_builder: Optional[Callable] = None
):
    """
    Cache database query results.

    Args:
        ttl: Cache TTL
        key_builder: Custom function to build cache key

    Usage:
        @cache_query(ttl=600)
        async def get_user_by_email(email: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Hash arguments for key
                arg_hash = hashlib.md5(
                    f"{args}{kwargs}".encode()
                ).hexdigest()[:12]
                cache_key = f"query:{func.__name__}:{arg_hash}"

            # Try cache
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Execute query
            result = await func(*args, **kwargs)

            # Cache if result is not None
            if result is not None:
                await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def rate_limit_cache(
    requests: int = 60,
    window: int = 60,
    key_func: Optional[Callable] = None,
    error_message: str = "Rate limit exceeded"
):
    """
    Rate limiting decorator using cache.

    Args:
        requests: Maximum requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key
        error_message: Error message when limit exceeded

    Usage:
        @rate_limit_cache(requests=10, window=60)
        async def api_endpoint(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build rate limit key
            if key_func:
                identifier = key_func(*args, **kwargs)
            else:
                # Default: use first argument or 'default'
                identifier = str(args[0]) if args else "default"

            cache_key = CacheKeys.rate_limit(identifier, f"{window}s")

            # Get current count
            current = await cache_manager.get(cache_key) or 0

            if current >= requests:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": error_message,
                        "retry_after": window
                    }
                )

            # Increment counter
            new_count = await cache_manager.incr(cache_key)

            # Set TTL on first request
            if new_count == 1:
                await cache_manager.expire(cache_key, window)

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def cache_aside(
    key_func: Callable,
    ttl: int = CacheKeys.TTL_DEFAULT,
    lock_timeout: int = 5
):
    """
    Cache-aside pattern with distributed locking.

    Prevents cache stampede by using locks when cache misses.

    Args:
        key_func: Function to generate cache key
        ttl: Cache TTL
        lock_timeout: Lock timeout in seconds

    Usage:
        @cache_aside(
            key_func=lambda user_id: f"user:{user_id}:expensive",
            ttl=3600
        )
        async def expensive_computation(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = key_func(*args, **kwargs)

            # Try cache first
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Acquire lock to prevent cache stampede
            lock_key = f"{cache_key}:lock"
            token = await cache_manager.acquire_lock(
                lock_key,
                timeout=lock_timeout,
                blocking=True,
                blocking_timeout=lock_timeout * 2
            )

            try:
                # Double-check cache after acquiring lock
                cached = await cache_manager.get(cache_key)
                if cached is not None:
                    return cached

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await cache_manager.set(cache_key, result, ttl=ttl)

                return result

            finally:
                # Release lock
                if token:
                    await cache_manager.release_lock(lock_key, token)

        return wrapper
    return decorator


def invalidate_cache(*patterns: str):
    """
    Invalidate cache patterns after function execution.

    Args:
        patterns: Cache key patterns to invalidate

    Usage:
        @invalidate_cache("user:{user_id}:*", "leaderboard")
        async def update_user_score(user_id: str, score: int):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            # Invalidate patterns
            for pattern in patterns:
                try:
                    # Format pattern with kwargs
                    formatted = pattern.format(**kwargs)

                    if "*" in formatted:
                        await cache_manager.delete_pattern(formatted)
                    else:
                        await cache_manager.delete(formatted)

                    logger.debug(f"Cache invalidated: {formatted}")
                except Exception as e:
                    logger.warning(f"Cache invalidation failed: {e}")

            return result

        return wrapper
    return decorator


def memoize(ttl: int = CacheKeys.TTL_LONG):
    """
    Memoize function results in cache.

    Creates a unique cache key based on function name and arguments.

    Args:
        ttl: Cache TTL

    Usage:
        @memoize(ttl=86400)
        async def compute_statistics(date: str):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create unique key from function and arguments
            key_data = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
            key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
            cache_key = f"memo:{func.__name__}:{key_hash}"

            # Try cache
            cached = await cache_manager.get(cache_key)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


class CacheManager:
    """
    Context manager for cache operations.

    Usage:
        async with CacheManager("user:123") as cache:
            data = await cache.get()
            if data is None:
                data = await expensive_operation()
                await cache.set(data, ttl=3600)
    """

    def __init__(self, key: str):
        self.key = key
        self._value = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get(self) -> Any:
        """Get cached value."""
        self._value = await cache_manager.get(self.key)
        return self._value

    async def set(self, value: Any, ttl: int = CacheKeys.TTL_DEFAULT) -> bool:
        """Set cached value."""
        return await cache_manager.set(self.key, value, ttl=ttl)

    async def delete(self) -> bool:
        """Delete cached value."""
        return await cache_manager.delete(self.key)

    async def exists(self) -> bool:
        """Check if key exists."""
        return await cache_manager.exists(self.key)
