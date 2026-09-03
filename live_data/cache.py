"""
Asynchronous TTL cache for market data and quant calculations.
Prevents duplicate API calls while maintaining data freshness.
"""

from __future__ import annotations

import time
import asyncio
from typing import Any, Dict, Optional, Tuple


class MarketDataCache:
    """Thread-safe in-memory cache with per-key TTL."""

    def __init__(self) -> None:
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key not in self._cache:
                return None
            expiry, value = self._cache[key]
            if time.time() > expiry:
                del self._cache[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        async with self._lock:
            self._cache[key] = (time.time() + ttl_seconds, value)

    async def invalidate(self, prefix: str = "") -> None:
        async with self._lock:
            if not prefix:
                self._cache.clear()
            else:
                keys_to_del = [k for k in self._cache if k.startswith(prefix)]
                for k in keys_to_del:
                    del self._cache[k]


# Global singleton cache instance
market_cache = MarketDataCache()
