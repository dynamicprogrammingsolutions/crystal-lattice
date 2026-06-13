from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, Hashable, List


ModelCacheKey = Hashable
ModelDescriptor = Dict[str, Any]
ModelDescriptorList = List[ModelDescriptor]


@dataclass(frozen=True)
class _ModelCacheEntry:
    value: ModelDescriptorList
    expires_at: float


class ModelDiscoveryCache:
    """Thread-safe cache for provider model discovery results.

    Empty results use a shorter TTL because some providers convert transient
    discovery failures into an empty list.
    """

    def __init__(
        self,
        *,
        success_ttl_seconds: float = 600.0,
        empty_ttl_seconds: float = 30.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._success_ttl_seconds = float(success_ttl_seconds)
        self._empty_ttl_seconds = float(empty_ttl_seconds)
        self._clock = clock or time.monotonic
        self._lock = threading.RLock()
        self._entries: Dict[ModelCacheKey, _ModelCacheEntry] = {}
        self._inflight: Dict[ModelCacheKey, threading.Condition] = {}

    def get_or_compute(
        self,
        key: ModelCacheKey,
        compute: Callable[[], ModelDescriptorList],
    ) -> ModelDescriptorList:
        """Return a cached value or compute it once for concurrent callers."""

        while True:
            with self._lock:
                cached = self._get_fresh_locked(key)
                if cached is not None:
                    return cached

                condition = self._inflight.get(key)
                if condition is None:
                    condition = threading.Condition(self._lock)
                    self._inflight[key] = condition
                    break

                condition.wait()

        try:
            value = compute()
        except Exception:
            with self._lock:
                condition = self._inflight.pop(key, None)
                if condition is not None:
                    condition.notify_all()
            raise

        ttl = self._success_ttl_seconds if value else self._empty_ttl_seconds
        with self._lock:
            if ttl > 0:
                self._entries[key] = _ModelCacheEntry(
                    value=value,
                    expires_at=self._clock() + ttl,
                )
            else:
                self._entries.pop(key, None)
            condition = self._inflight.pop(key, None)
            if condition is not None:
                condition.notify_all()
        return value

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _get_fresh_locked(self, key: ModelCacheKey) -> ModelDescriptorList | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at <= self._clock():
            self._entries.pop(key, None)
            return None
        return entry.value