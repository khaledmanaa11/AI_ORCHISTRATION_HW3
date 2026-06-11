from __future__ import annotations

import os

from reasearch_crew import settings
from reasearch_crew.gateway import http_post

_SEARCH_TIMEOUT = 20.0
_unverified = False


def is_unverified() -> bool:
    """True if the last search ran without a key (results are ungrounded)."""
    return _unverified


def web_search(query: str, *, max_results: int = 5) -> list[dict]:
    """Search the web through the gateway's Serper egress seam (§5.1).

    Returns normalized ``[{title, url, snippet}]``. With no ``SERPER_API_KEY``
    set, returns ``[]`` and flips :func:`is_unverified` — the report then falls
    back to LLM-only content behind a "נתונים לא מאומתים" banner (R-AC2).
    """
    global _unverified
    key = os.getenv("SERPER_API_KEY")
    if not key:
        _unverified = True
        return []
    _unverified = False

    data = http_post(
        settings.endpoint("serper"),
        headers={"X-API-KEY": key, "Content-Type": "application/json"},
        json={"q": query, "num": max_results},
        provider="serper",
        timeout=_SEARCH_TIMEOUT,
    )
    organic = data.get("organic", []) if isinstance(data, dict) else []
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in organic[:max_results]
    ]
