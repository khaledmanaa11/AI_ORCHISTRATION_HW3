import pytest

from reasearch_crew.gateway import config as gw_config
from reasearch_crew.gateway import rate_limiter


@pytest.fixture(autouse=True)
def _reset_state():
    rate_limiter.reset()
    gw_config.reset_cache()
    yield
    rate_limiter.reset()
    gw_config.reset_cache()


def test_config_loaded_from_json():
    cfg = gw_config.provider("openrouter")
    assert cfg["rpm"] == 20
    assert cfg["burst"] == 5


def test_first_call_no_sleep(monkeypatch):
    monkeypatch.setattr(rate_limiter.time, "sleep", lambda s: None)
    waited = rate_limiter.acquire("openrouter")
    assert waited == 0.0


def test_token_bucket_sleeps_when_empty(monkeypatch):
    """R-AC3: at 1 RPS, two calls sleep ~1s on the second."""
    fake_now = [0.0]
    slept: list[float] = []

    def fake_monotonic():
        return fake_now[0]

    def fake_sleep(s):
        slept.append(s)
        fake_now[0] += s

    monkeypatch.setattr(rate_limiter.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(rate_limiter.time, "sleep", fake_sleep)
    monkeypatch.setattr(
        gw_config,
        "provider",
        lambda name: {"rpm": 60, "burst": 1},
    )

    rate_limiter.acquire("openrouter")
    rate_limiter.acquire("openrouter")
    assert slept == pytest.approx([1.0], abs=0.01)


def test_burst_allows_multiple_then_throttles(monkeypatch):
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
        lambda name: {"rpm": 60, "burst": 3},
    )

    for _ in range(3):
        rate_limiter.acquire("anthropic")
    assert slept == []
    rate_limiter.acquire("anthropic")
    assert slept and slept[0] > 0


def test_unknown_provider_raises(monkeypatch):
    with pytest.raises(KeyError):
        rate_limiter.acquire("ghost-provider-xyz")


def test_invalid_rpm_raises(monkeypatch):
    monkeypatch.setattr(
        gw_config, "provider", lambda name: {"rpm": 0, "burst": 1}
    )
    with pytest.raises(ValueError):
        rate_limiter.acquire("broken")


def test_independent_buckets_per_provider(monkeypatch):
    fake_now = [0.0]
    monkeypatch.setattr(rate_limiter.time, "monotonic", lambda: fake_now[0])
    monkeypatch.setattr(rate_limiter.time, "sleep", lambda s: None)

    def fake(name):
        return {"rpm": 60, "burst": 1}

    monkeypatch.setattr(gw_config, "provider", fake)

    assert rate_limiter.acquire("openrouter") == 0.0
    assert rate_limiter.acquire("anthropic") == 0.0
