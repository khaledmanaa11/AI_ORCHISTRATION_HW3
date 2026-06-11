import httpx
import litellm
import pytest

from reasearch_crew.gateway.errors import (
    AuthError,
    BadRequest,
    GatewayError,
    ProviderUnavailable,
    RateLimitExceeded,
    from_provider_exception,
)


def _llm_err(cls, msg="boom"):
    kwargs = {"message": msg, "llm_provider": "openrouter", "model": "x"}
    try:
        return cls(**kwargs)
    except TypeError:
        req = httpx.Request("POST", "https://example.test")
        return cls(response=httpx.Response(400, request=req), **kwargs)


@pytest.mark.parametrize(
    "litellm_cls,expected",
    [
        (litellm.RateLimitError, RateLimitExceeded),
        (litellm.AuthenticationError, AuthError),
        (litellm.PermissionDeniedError, AuthError),
        (litellm.ServiceUnavailableError, ProviderUnavailable),
        (litellm.InternalServerError, ProviderUnavailable),
        (litellm.BadGatewayError, ProviderUnavailable),
        (litellm.BadRequestError, BadRequest),
        (litellm.NotFoundError, BadRequest),
        (litellm.UnprocessableEntityError, BadRequest),
    ],
)
def test_litellm_translation_table(litellm_cls, expected):
    exc = _llm_err(litellm_cls)
    assert isinstance(from_provider_exception(exc), expected)


def test_litellm_api_connection_translates_to_provider_unavailable():
    exc = litellm.APIConnectionError(
        message="net dead", llm_provider="openrouter", model="x"
    )
    assert isinstance(from_provider_exception(exc), ProviderUnavailable)


@pytest.mark.parametrize(
    "status,expected",
    [
        (401, AuthError),
        (403, AuthError),
        (400, BadRequest),
        (404, BadRequest),
        (422, BadRequest),
        (429, RateLimitExceeded),
        (500, ProviderUnavailable),
        (503, ProviderUnavailable),
        (504, ProviderUnavailable),
    ],
)
def test_httpx_status_error_translation(status, expected):
    req = httpx.Request("POST", "https://example.test")
    resp = httpx.Response(status, request=req)
    err = httpx.HTTPStatusError("bad", request=req, response=resp)
    assert isinstance(from_provider_exception(err), expected)


def test_httpx_connect_error_translates_to_provider_unavailable():
    err = httpx.ConnectError("dns")
    assert isinstance(from_provider_exception(err), ProviderUnavailable)


def test_httpx_timeout_translates_to_provider_unavailable():
    err = httpx.TimeoutException("slow")
    assert isinstance(from_provider_exception(err), ProviderUnavailable)


def test_gateway_error_passes_through():
    err = RateLimitExceeded("already domain")
    assert from_provider_exception(err) is err


def test_unknown_status_falls_through_to_gateway_error():
    class _FakeExc(Exception):
        status_code = 418

    result = from_provider_exception(_FakeExc("teapot"))
    assert isinstance(result, GatewayError)
    assert not isinstance(result, (AuthError, BadRequest, RateLimitExceeded))


def test_unmapped_exception_returns_gateway_error():
    result = from_provider_exception(ValueError("nope"))
    assert isinstance(result, GatewayError)


def test_hierarchy_is_correct():
    for cls in (RateLimitExceeded, ProviderUnavailable, AuthError, BadRequest):
        assert issubclass(cls, GatewayError)
