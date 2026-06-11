from __future__ import annotations

from typing import Any

import httpx

from . import rate_limiter, retry, telemetry
from .errors import from_provider_exception


def _do_post(
    url: str,
    headers: dict[str, str] | None,
    json: dict[str, Any] | None,
    timeout: float,
) -> dict[str, Any]:
    try:
        response = httpx.post(
            url, headers=headers, json=json, timeout=timeout
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise from_provider_exception(exc) from exc
    except httpx.HTTPError as exc:
        raise from_provider_exception(exc) from exc
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text}


def http_post(
    url: str,
    headers: dict[str, str] | None = None,
    json: dict[str, Any] | None = None,
    *,
    provider: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """POST to `url` under the gateway's rate-limit / retry / telemetry stack.

    All non-LLM external HTTP calls must go through this function.
    """
    rate_limiter.acquire(provider)

    def _call():
        return _do_post(url, headers, json, timeout)

    try:
        result = retry.run(provider, _call)
    except Exception:
        telemetry.record_call(provider)
        raise
    telemetry.record_call(provider)
    return result
