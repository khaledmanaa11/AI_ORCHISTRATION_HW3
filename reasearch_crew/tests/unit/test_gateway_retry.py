import litellm
import pytest

from reasearch_crew.gateway import config as gw_config
from reasearch_crew.gateway import retry as gw_retry
from reasearch_crew.gateway.errors import (
    AuthError,
    BadRequest,
    RateLimitExceeded,
)


@pytest.fixture(autouse=True)
def _fast_policy(monkeypatch):
    monkeypatch.setattr(
        gw_config,
        "retry_policy",
        lambda: {"max_attempts": 3, "base_delay_sec": 0.0001, "jitter": "full"},
    )
    yield


def _ratelimit():
    return litellm.RateLimitError(
        message="429", llm_provider="openrouter", model="x"
    )


def _autherr():
    return litellm.AuthenticationError(
        message="401", llm_provider="openrouter", model="x"
    )


def test_three_retries_then_raise():
    """R-AC2: 3 retries, 4th attempt raises RateLimitExceeded."""
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise _ratelimit()

    with pytest.raises(RateLimitExceeded):
        gw_retry.run("openrouter", fn)
    assert calls["n"] == 4


def test_auth_error_no_retry():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise _autherr()

    with pytest.raises(AuthError):
        gw_retry.run("openrouter", fn)
    assert calls["n"] == 1


def test_bad_request_no_retry():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        raise litellm.BadRequestError(
            message="bad", llm_provider="openrouter", model="x"
        )

    with pytest.raises(BadRequest):
        gw_retry.run("openrouter", fn)
    assert calls["n"] == 1


def test_success_no_retry():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        return "ok"

    assert gw_retry.run("openrouter", fn) == "ok"
    assert calls["n"] == 1


def test_eventual_success_after_retries():
    calls = {"n": 0}

    def fn():
        calls["n"] += 1
        if calls["n"] < 3:
            raise _ratelimit()
        return "finally"

    assert gw_retry.run("openrouter", fn) == "finally"
    assert calls["n"] == 3


def test_gateway_error_subclass_propagates():
    def fn():
        raise RateLimitExceeded("direct")

    with pytest.raises(RateLimitExceeded):
        gw_retry.run("openrouter", fn)


def test_unknown_exception_translates_to_gateway_error():
    from reasearch_crew.gateway.errors import GatewayError

    def fn():
        raise ValueError("strange")

    with pytest.raises(GatewayError):
        gw_retry.run("openrouter", fn)
