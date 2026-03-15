"""Cache service catalog — auto-imports all cache service definitions."""

from __future__ import annotations

from pyworkspace.catalog.cache.memcached import MemcachedService
from pyworkspace.catalog.cache.redis_cache import RedisCacheService

__all__ = [
    "MemcachedService",
    "RedisCacheService",
]
