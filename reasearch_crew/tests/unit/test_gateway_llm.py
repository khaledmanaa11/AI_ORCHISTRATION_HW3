import litellm
import pytest

from reasearch_crew.gateway import (
    config as gw_config,
    rate_limiter,
    telemetry,
)
from reasearch_crew.gateway.errors import AuthError, RateLimitExceeded
from reasearch_crew.gateway.llm import GatekeptLLM, _provider_from_model


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    rate_limiter.reset()
    telemetry.reset()
    gw_config.reset_cache()
    monkeypatch.setattr(
        gw_config,
        "retry_policy",
        lambda: {"max_attempts": 3, "base_delay_sec": 0.0001, "jitter": "full"},
    )
    yield
    rate_limiter.reset()
    telemetry.reset()
    gw_config.reset_cache()


def _make_llm():
    return GatekeptLLM(
        model="gemini/gemini-2.0-flash",
        base_url="",
        api_key="sk-test",
    )


def test_provider_from_model_strips_prefix():
    assert _provider_from_model("openrouter/anything/here") == "openrouter"
    assert _provider_from_model("gemini/gemini-2.0-flash") == "gemini"
    assert _provider_from_model("anthropic/claude") == "anthropic"
    assert _provider_from_model("local") == "local"


def test_call_increments_telemetry(monkeypatch):
    from crewai import LLM

    monkeypatch.setattr(
        LLM, "call", lambda self, *a, **kw: {"choices": [{"message": "hi"}]}
    )
    llm = _make_llm()
    llm.call([{"role": "user", "content": "ping"}])
    snap = telemetry.snapshot()
    assert snap["gemini"]["calls"] == 1


def test_call_records_token_usage(monkeypatch):
    from crewai import LLM

    monkeypatch.setattr(
        LLM,
        "call",
        lambda self, *a, **kw: {
            "choices": [{"message": "hi"}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 7},
        },
    )
    _make_llm().call([{"role": "user", "content": "ping"}])
    snap = telemetry.snapshot()
    assert snap["gemini"]["input_tokens"] == 5
    assert snap["gemini"]["output_tokens"] == 7


def test_call_retries_on_429(monkeypatch):
    from crewai import LLM

    calls = {"n": 0}

    def fake(self, *a, **kw):
        calls["n"] += 1
        if calls["n"] < 2:
            raise litellm.RateLimitError(
                message="429", llm_provider="gemini", model="x"
            )
        return "ok"

    monkeypatch.setattr(LLM, "call", fake)
    out = _make_llm().call([{"role": "user", "content": "x"}])
    assert out == "ok"
    assert calls["n"] == 2
    assert telemetry.snapshot()["gemini"]["retries"] == 1


def test_call_translates_auth_error(monkeypatch):
    from crewai import LLM

    def raise_auth(self, *a, **kw):
        raise litellm.AuthenticationError(
            message="401", llm_provider="gemini", model="x"
        )

    monkeypatch.setattr(LLM, "call", raise_auth)
    with pytest.raises(AuthError):
        _make_llm().call([{"role": "user", "content": "x"}])


def test_call_raises_rate_limit_after_retries(monkeypatch):
    from crewai import LLM

    def always_429(self, *a, **kw):
        raise litellm.RateLimitError(
            message="429", llm_provider="gemini", model="x"
        )

    monkeypatch.setattr(LLM, "call", always_429)
    with pytest.raises(RateLimitExceeded):
        _make_llm().call([{"role": "user", "content": "x"}])


def test_completion_alias_routes_through_call(monkeypatch):
    from crewai import LLM

    monkeypatch.setattr(LLM, "call", lambda self, *a, **kw: "done")
    out = _make_llm().completion([{"role": "user", "content": "x"}])
    assert out == "done"
    assert telemetry.snapshot()["gemini"]["calls"] == 1


def test_token_counts_handles_object_usage(monkeypatch):
    from crewai import LLM

    class _U:
        prompt_tokens = 3
        completion_tokens = 4

    class _R:
        usage = _U()

    monkeypatch.setattr(LLM, "call", lambda self, *a, **kw: _R())
    _make_llm().call([{"role": "user", "content": "x"}])
    snap = telemetry.snapshot()
    assert snap["gemini"]["input_tokens"] == 3
    assert snap["gemini"]["output_tokens"] == 4
