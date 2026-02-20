"""
Services package initialization.
Provides base service class and caching utilities.
"""
from flask import current_app
from typing import Optional, Callable, Any
from functools import wraps
import hashlib
import json


class BaseService:
    """Base service class with common functionality."""
    
    def __init__(self) -> None:
        """Initialize service."""
        self.cache = None
        if current_app:
            from flask_caching import Cache
            self.cache = current_app.extensions.get('cache')
    
    def get_cache_key(self, *args: Any, **kwargs: Any) -> str:
        """Generate cache key from arguments."""
        key_data = f"{self.__class__.__name__}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def invalidate_cache(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        if self.cache:
            try:
                self.cache.delete_memoized(pattern)
            except Exception as e:
                print(f"Cache invalidation error: {e}")


def cache_result(timeout: int = 300, key_prefix: Optional[str] = None) -> Callable:
    """
    Decorator to cache function results in Redis.
    
    Args:
        timeout: Cache timeout in seconds (default 5 minutes)
        key_prefix: Optional prefix for cache key
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get cache from Flask app
            cache = None
            if current_app:
                cache = current_app.extensions.get('cache')
            
            # Check if cache is dict (misconfigured) or None
            if not cache or isinstance(cache, dict):
                # No cache available or misconfigured, call function directly
                return f(*args, **kwargs)
            
            # Verify cache has required methods
            if not (hasattr(cache, 'get') and hasattr(cache, 'set')):
                return f(*args, **kwargs)
            
            # Generate cache key
            prefix = key_prefix or f.__name__
            key_data = f"{prefix}:{args}:{json.dumps(kwargs, sort_keys=True)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            try:
                # Try to get from cache
                cached = cache.get(cache_key)
                if cached is not None:
                    return cached
                
                # Not in cache, call function
                result = f(*args, **kwargs)
                
                # Store in cache
                cache.set(cache_key, result, timeout=timeout)
                return result
            except Exception as e:
                # If caching fails, just call the function
                print(f"Cache error: {e}")
                return f(*args, **kwargs)
        
        return wrapper
    return decorator


def invalidate_cache_pattern(pattern: str) -> None:
    """
    Invalidate all cache entries matching pattern.
    
    Args:
        pattern: Pattern to match cache keys (e.g., 'blog:*', 'project:*')
    """
    cache = None
    if current_app:
        cache = current_app.extensions.get('cache')
    
    # Skip if no cache or cache is misconfigured
    if not cache or isinstance(cache, dict):
        return
    
    if hasattr(cache, 'cache') and hasattr(cache.cache, 'delete_many'):
        try:
            # Redis-specific: delete all keys matching pattern
            cache.cache.delete_many(pattern)
        except Exception as e:
            print(f"Cache pattern invalidation error: {e}")
    elif hasattr(cache, 'clear'):
        # Fallback: clear all cache
        try:
            cache.clear()
        except Exception as e:
            print(f"Cache clear error: {e}")
