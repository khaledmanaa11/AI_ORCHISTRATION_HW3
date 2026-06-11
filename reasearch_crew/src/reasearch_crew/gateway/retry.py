from __future__ import annotations

import logging
from typing import Any, Callable

from tenacity import (
    RetryError,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

from . import config as _config
from .errors import (
    AuthError,
    BadRequest,
    GatewayError,
    ProviderUnavailable,
    RateLimitExceeded,
    from_provider_exception,
)

_log = logging.getLogger("gateway.retry")

_RETRYABLE = (RateLimitExceeded, ProviderUnavailable)
_NON_RETRYABLE = (AuthError, BadRequest)


def _should_retry(exc: BaseException) -> bool:
    domain = (
        exc if isinstance(exc, GatewayError) else from_provider_exception(exc)
    )
    if isinstance(domain, _NON_RETRYABLE):
        return False
    return isinstance(domain, _RETRYABLE)


def _log_attempt(provider: str):
    def _hook(state):
        exc = state.outcome.exception() if state.outcome else None
        if exc is not None:
            _log.warning(
                "gateway: retry attempt %d for %s: %s",
                state.attempt_number,
                provider,
                exc,
            )

    return _hook


def run(provider: str, fn: Callable[[], Any]) -> Any:
    """Execute fn() with the retry policy for `provider`.

    Translates the final provider exception into a GatewayError.
    """
    policy = _config.retry_policy()
    max_attempts = int(policy["max_attempts"]) + 1
    base = float(policy["base_delay_sec"])

    retrying = Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_random_exponential(multiplier=base, max=base * 16),
        retry=retry_if_exception(_should_retry),
        before_sleep=_log_attempt(provider),
        reraise=True,
    )
    try:
        for attempt in retrying:
            with attempt:
                return fn()
    except RetryError as re:
        raise from_provider_exception(re.last_attempt.exception()) from re
    except GatewayError:
        raise
    except Exception as exc:
        raise from_provider_exception(exc) from exc
