from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float


class TTLCache(Generic[T]):
    def __init__(self, ttl_s: float = 300.0, max_items: int = 128):
        self.ttl_s = ttl_s
        self.max_items = max_items
        self._store: Dict[str, _Entry[T]] = {}

    def get(self, key: str) -> Optional[T]:
        e = self._store.get(key)
        if not e:
            return None
        if e.expires_at < time.time():
            self._store.pop(key, None)
            return None
        return e.value

    def set(self, key: str, value: T) -> None:
        if len(self._store) >= self.max_items:
            # naive eviction: remove oldest expiry
            oldest = min(self._store.items(), key=lambda kv: kv[1].expires_at)[0]
            self._store.pop(oldest, None)
        self._store[key] = _Entry(value=value, expires_at=time.time() + self.ttl_s)

    async def get_or_set(self, key: str, factory: Callable[[], "T | object"], /):
        v = self.get(key)
        if v is not None:
            return v
        created = factory()
        # allow async factory
        if hasattr(created, "__await__"):
            created = await created  # type: ignore[assignment]
        self.set(key, created)  # type: ignore[arg-type]
        return created
