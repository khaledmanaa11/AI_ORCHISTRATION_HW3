import pytest

from reasearch_crew.tools import search


@pytest.fixture(autouse=True)
def _clear_flag():
    search._unverified = False
    yield
    search._unverified = False


def test_routes_through_gateway(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, *, provider, timeout=30.0):
        captured["url"] = url
        captured["provider"] = provider
        captured["query"] = json["q"]
        return {
            "organic": [
                {"title": "T1", "link": "https://a", "snippet": "S1"},
                {"title": "T2", "link": "https://b", "snippet": "S2"},
            ]
        }

    monkeypatch.setattr(search, "http_post", fake_post)
    monkeypatch.setenv("SERPER_API_KEY", "serper-test-key")

    out = search.web_search("ALYASMEEN market size", max_results=2)

    assert captured["provider"] == "serper"
    assert captured["url"].startswith("https://")
    assert captured["query"] == "ALYASMEEN market size"
    assert out == [
        {"title": "T1", "url": "https://a", "snippet": "S1"},
        {"title": "T2", "url": "https://b", "snippet": "S2"},
    ]
    assert search.is_unverified() is False


def test_missing_key_fallback(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)

    def explode(*a, **k):
        raise AssertionError("must not hit the gateway without a key")

    monkeypatch.setattr(search, "http_post", explode)

    out = search.web_search("anything")

    assert out == []
    assert search.is_unverified() is True


def test_respects_max_results(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setattr(
        search,
        "http_post",
        lambda *a, **k: {"organic": [{"title": str(i)} for i in range(10)]},
    )
    assert len(search.web_search("q", max_results=3)) == 3
