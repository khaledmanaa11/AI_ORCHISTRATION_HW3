from __future__ import annotations

import json
from pathlib import Path

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "rate_limits.json"
)
_cache: dict | None = None


def load(force: bool = False) -> dict:
    """Read rate_limits.json once and memoize. Call with force=True in tests."""
    global _cache
    if _cache is None or force:
        _cache = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    return _cache


def provider(name: str) -> dict:
    cfg = load()
    try:
        return cfg["providers"][name]
    except KeyError as exc:
        raise KeyError(
            f"provider '{name}' missing from rate_limits.json"
        ) from exc


def retry_policy() -> dict:
    return load()["retry"]


def reset_cache() -> None:
    global _cache
    _cache = None
