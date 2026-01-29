# cache_utils.py
# FlyReady Lab - Centralized Caching Utilities
# Provides consistent caching across all pages

import streamlit as st
import json
import os
import time
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime

# In-memory cache for frequently accessed data
_memory_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_json(filepath: str, ttl_seconds: int = 60, default: Any = None) -> Any:
    """
    Load JSON file with in-memory caching.
    
    Args:
        filepath: Path to JSON file
        ttl_seconds: Cache TTL in seconds (default 60)
        default: Default value if file not found or error
    
    Returns:
        Parsed JSON data or default value
    """
    cache_key = f'json:{filepath}'
    now = time.time()
    
    # Check memory cache
    if cache_key in _memory_cache:
        cached = _memory_cache[cache_key]
        if now - cached['time'] < ttl_seconds:
            return cached['data']
    
    # Load from file
    if default is None:
        default = {}
    
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _memory_cache[cache_key] = {'data': data, 'time': now}
            return data
        except (json.JSONDecodeError, IOError) as e:
            return default
    
    return default


def invalidate_cache(filepath: str = None):
    """
    Invalidate cache for a specific file or all files.
    
    Args:
        filepath: Specific file to invalidate (None = all)
    """
    global _memory_cache
    if filepath:
        cache_key = f'json:{filepath}'
        if cache_key in _memory_cache:
            del _memory_cache[cache_key]
    else:
        _memory_cache.clear()


def save_json_and_invalidate(filepath: str, data: Any):
    """
    Save JSON and invalidate its cache.
    
    Args:
        filepath: Path to JSON file
        data: Data to save
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        invalidate_cache(filepath)
    except IOError as e:
        pass


@st.cache_data(ttl=300)
def get_static_data(filepath: str) -> Any:
    """
    Load static data with Streamlit caching (5 min TTL).
    Use for data that rarely changes.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


@st.cache_resource
def get_resource_data(filepath: str) -> Any:
    """
    Load resource data with permanent caching.
    Use for config files that never change during session.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def with_loading_indicator(message: str = '로딩 중...'):
    """
    Decorator to show loading indicator during function execution.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class CacheStats:
    """Track cache statistics for debugging."""
    hits = 0
    misses = 0
    
    @classmethod
    def hit(cls):
        cls.hits += 1
    
    @classmethod
    def miss(cls):
        cls.misses += 1
    
    @classmethod
    def ratio(cls) -> float:
        total = cls.hits + cls.misses
        return cls.hits / total if total > 0 else 0.0
