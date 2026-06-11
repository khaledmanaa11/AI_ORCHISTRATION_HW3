from __future__ import annotations


class GatewayError(Exception):
    """Base class for every error the gateway surfaces to callers."""


class RateLimitExceeded(GatewayError):
    """Raised when retries have been exhausted on a 429."""


class ProviderUnavailable(GatewayError):
    """Raised when retries have been exhausted on a 5xx / connection error."""


class AuthError(GatewayError):
    """Raised for 401 / 403. Not retried — the key is misconfigured."""


class BadRequest(GatewayError):
    """Raised for 400 / 404. Not retried — the request itself is wrong."""


_RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


def _status_to_gateway(status: int, message: str) -> GatewayError:
    if status in {401, 403}:
        return AuthError(message)
    if status in {400, 404, 422}:
        return BadRequest(message)
    if status == 429:
        return RateLimitExceeded(message)
    if 500 <= status < 600:
        return ProviderUnavailable(message)
    return GatewayError(f"unmapped status {status}: {message}")


def from_provider_exception(exc: BaseException) -> GatewayError:
    """Translate a provider-specific exception into our stable hierarchy."""
    if isinstance(exc, GatewayError):
        return exc

    status = getattr(exc, "status_code", None)
    if status is None:
        response = getattr(exc, "response", None)
        status = getattr(response, "status_code", None)

    message = str(exc) or exc.__class__.__name__

    try:
        import litellm
    except ImportError:
        litellm = None

    if litellm is not None:
        if isinstance(exc, litellm.RateLimitError):
            return RateLimitExceeded(message)
        if isinstance(exc, litellm.AuthenticationError):
            return AuthError(message)
        if isinstance(exc, getattr(litellm, "PermissionDeniedError", ())):
            return AuthError(message)
        if isinstance(
            exc,
            (
                litellm.ServiceUnavailableError,
                litellm.InternalServerError,
                getattr(litellm, "BadGatewayError", ()),
                litellm.APIConnectionError,
            ),
        ):
            return ProviderUnavailable(message)
        if isinstance(
            exc,
            (
                litellm.BadRequestError,
                litellm.NotFoundError,
                getattr(litellm, "UnprocessableEntityError", ()),
            ),
        ):
            return BadRequest(message)

    try:
        import httpx
    except ImportError:
        httpx = None

    if httpx is not None:
        if isinstance(exc, httpx.HTTPStatusError):
            return _status_to_gateway(exc.response.status_code, message)
        if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
            return ProviderUnavailable(message)

    if isinstance(status, int):
        return _status_to_gateway(status, message)

    return GatewayError(message)
