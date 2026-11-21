"""In-memory cache and token telemetry for RailNiyam.
Provides thread-safe caching of RAG query responses with LRU eviction and token metrics.
"""
from __future__ import annotations

import math
import re
import threading
import time
from typing import Any


def normalize_query(query: str) -> str:
    """Normalize query text for consistent cache key mapping."""
    q = query.lower().strip()
    q = re.sub(r"\s+", " ", q)
    q = re.sub(r"[^\w\s]", "", q)
    return q


def estimate_tokens(text: str) -> int:
    """Fast, reliable heuristic token counter (~4 chars per token / 1.3 words per token)."""
    if not text:
        return 0
    words = len(text.split())
    by_words = math.ceil(words * 1.3)
    by_chars = math.ceil(len(text) / 4)
    return max(1, max(by_words, by_chars))


class QueryCache:
    """Thread-safe in-memory cache with eviction and hit/miss statistics."""

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 3600.0) -> None:
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()
        self.hits: int = 0
        self.misses: int = 0

    def get(self, query: str) -> dict[str, Any] | None:
        key = normalize_query(query)
        with self._lock:
            if key not in self._cache:
                self.misses += 1
                return None

            entry = self._cache[key]
            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl:
                del self._cache[key]
                self.misses += 1
                return None

            self.hits += 1
            return entry["data"]

    def set(self, query: str, data: dict[str, Any]) -> None:
        key = normalize_query(query)
        with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                # Evict oldest entry
                oldest_key = min(self._cache, key=lambda k: self._cache[k]["timestamp"])
                del self._cache[oldest_key]

            self._cache[key] = {
                "timestamp": time.time(),
                "data": data,
            }

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate_pct": round(hit_rate, 2),
            }


# Global shared query cache instance
QUERY_CACHE = QueryCache()

