import httpx
import pytest

from reasearch_crew.gateway import (
    config as gw_config,
    http as gw_http,
    rate_limiter,
    telemetry,
)
from reasearch_crew.gateway.errors import (
    AuthError,
    ProviderUnavailable,
)


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
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


def _ok_response(body=None):
    req = httpx.Request("POST", "https://example.test/x")
    return httpx.Response(200, json=body or {"ok": True}, request=req)


def _err_response(status):
    req = httpx.Request("POST", "https://example.test/x")
    return httpx.Response(status, request=req, json={"err": status})


def test_http_post_returns_json(monkeypatch):
    monkeypatch.setattr(
        gw_http.httpx, "post", lambda *a, **kw: _ok_response({"hello": "world"})
    )
    out = gw_http.http_post(
        "https://example.test/x",
        headers={"x": "1"},
        json={"q": "a"},
        provider="serper",
    )
    assert out == {"hello": "world"}
    assert telemetry.snapshot()["serper"]["calls"] == 1


def test_http_post_translates_auth_error(monkeypatch):
    monkeypatch.setattr(gw_http.httpx, "post", lambda *a, **kw: _err_response(401))
    with pytest.raises(AuthError):
        gw_http.http_post(
            "https://example.test/x", provider="serper", json={}
        )


def test_http_post_retries_503_then_succeeds(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **kw):
        calls["n"] += 1
        if calls["n"] < 2:
            return _err_response(503)
        return _ok_response({"ok": True})

    monkeypatch.setattr(gw_http.httpx, "post", fake_post)
    out = gw_http.http_post(
        "https://example.test/x", provider="serper", json={}
    )
    assert out == {"ok": True}
    assert calls["n"] == 2


def test_http_post_503_exhausts_retries(monkeypatch):
    calls = {"n": 0}

    def fake_post(*a, **kw):
        calls["n"] += 1
        return _err_response(503)

    monkeypatch.setattr(gw_http.httpx, "post", fake_post)
    with pytest.raises(ProviderUnavailable):
        gw_http.http_post(
            "https://example.test/x", provider="serper", json={}
        )
    assert calls["n"] == 4


def test_http_post_respects_rate_limit(monkeypatch):
    """R-AC4: at 1 RPS, two calls space ~1s apart."""
    fake_now = [0.0]
    slept: list[float] = []

    monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: fake_now[0])
    monkeypatch.setattr(
        rate_limiter.time,
        "sleep",
        lambda s: (slept.append(s), fake_now.__setitem__(0, fake_now[0] + s)),
    )
    monkeypatch.setattr(
        gw_config,
        "provider",
        lambda name: {"rpm": 60, "burst": 1},
    )
    monkeypatch.setattr(gw_http.httpx, "post", lambda *a, **kw: _ok_response())

    gw_http.http_post(
        "https://example.test/x", provider="serper", json={}
    )
    gw_http.http_post(
        "https://example.test/x", provider="serper", json={}
    )
    assert slept == pytest.approx([1.0], abs=0.01)


def test_non_json_response_returned_as_raw(monkeypatch):
    req = httpx.Request("POST", "https://example.test/x")
    resp = httpx.Response(200, text="plain text", request=req)
    monkeypatch.setattr(gw_http.httpx, "post", lambda *a, **kw: resp)
    out = gw_http.http_post(
        "https://example.test/x", provider="serper", json={}
    )
    assert out == {"raw": "plain text"}


def test_connect_error_translates(monkeypatch):
    def boom(*a, **kw):
        raise httpx.ConnectError("dns")

    monkeypatch.setattr(gw_http.httpx, "post", boom)
    with pytest.raises(ProviderUnavailable):
        gw_http.http_post(
            "https://example.test/x", provider="serper", json={}
        )
