from __future__ import annotations

import time
from dataclasses import dataclass

from . import config as _config


@dataclass
class _Bucket:
    capacity: int
    rate_per_sec: float
    tokens: float
    updated_at: float

    def take(self, now: float) -> float:
        """Return seconds to sleep before a token is available; consume one."""
        elapsed = max(0.0, now - self.updated_at)
        self.tokens = min(
            float(self.capacity), self.tokens + elapsed * self.rate_per_sec
        )
        self.updated_at = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return 0.0
        deficit = 1.0 - self.tokens
        wait = deficit / self.rate_per_sec
        self.tokens = 0.0
        self.updated_at = now + wait
        return wait


_buckets: dict[str, _Bucket] = {}


def _build_bucket(name: str) -> _Bucket:
    cfg = _config.provider(name)
    rpm = int(cfg["rpm"])
    burst = int(cfg.get("burst", 1))
    if rpm <= 0:
        raise ValueError(f"provider {name} has non-positive rpm {rpm}")
    return _Bucket(
        capacity=burst,
        rate_per_sec=rpm / 60.0,
        tokens=float(burst),
        updated_at=time.monotonic(),
    )


def acquire(provider: str) -> float:
    """Block until a token is free for `provider`; return seconds slept."""
    bucket = _buckets.get(provider)
    if bucket is None:
        bucket = _build_bucket(provider)
        _buckets[provider] = bucket
    wait = bucket.take(time.monotonic())
    if wait > 0:
        time.sleep(wait)
    return wait


def reset() -> None:
    """Clear all buckets — for tests."""
    _buckets.clear()
