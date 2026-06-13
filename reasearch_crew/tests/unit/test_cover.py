import base64
from pathlib import Path

import pytest

from reasearch_crew import settings
from reasearch_crew.gateway import load_llm_config
from reasearch_crew.report import assemble, cover
from reasearch_crew.report.dataset import Dataset, Figure

_PNG = b"\x89PNG\r\n\x1a\n-fake-bytes"


def _fig(name, value, unit="x"):
    return Figure(name=name, value=value, unit=unit, source="https://s/x", label="")


@pytest.fixture
def ds():
    return Dataset(
        figures=(
            _fig("tam", 1_200_000_000, "USD"),
            _fig("sam_share", 0.25),
            _fig("som_share", 0.10),
            _fig("arpu", 20.0, "USD/mo"),
            _fig("gross_margin", 0.80),
            _fig("churn", 0.05, "/mo"),
            _fig("marketing_spend", 50_000, "USD"),
            _fig("customers_acquired", 500, "count"),
        )
    )


@pytest.fixture
def assets(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "asset_dir", lambda: tmp_path)
    return tmp_path


def test_routes_through_gateway_and_writes_png(assets, monkeypatch):
    captured = {}
    key_env = load_llm_config()["key_envs"]["typeset"]

    def fake_post(url, headers=None, json=None, *, provider, timeout=30.0):
        captured["url"] = url
        captured["key"] = headers["x-goog-api-key"]
        captured["provider"] = provider
        captured["prompt"] = json["instances"][0]["prompt"]
        return {"predictions": [{"bytesBase64Encoded": base64.b64encode(_PNG).decode()}]}

    monkeypatch.setattr(cover, "http_post", fake_post)
    monkeypatch.setenv(key_env, "typeset-key")

    out = cover.generate_cover()

    # (a) the call left report/ through the gateway under the image provider
    assert captured["provider"] == "gemini_image"
    assert captured["key"] == "typeset-key"
    assert captured["url"].startswith("https://")
    assert "<model>" not in captured["url"]  # model substituted from config
    assert settings.book_config()["title"] in captured["prompt"]
    # (b) the base64 payload was decoded and written at paths.cover
    cover_name = settings.book_config()["paths"]["cover"]
    assert out == assets / cover_name
    assert out.read_bytes() == _PNG


def test_missing_key_returns_fallback_without_calling(assets, monkeypatch):
    key_env = load_llm_config()["key_envs"]["typeset"]
    monkeypatch.delenv(key_env, raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "retired-shared-key")

    def explode(*a, **k):
        raise AssertionError("must not hit the gateway without a key")

    monkeypatch.setattr(cover, "http_post", explode)

    out = cover.generate_cover()

    # (c) bundled alyasmeen.png path, no http_post call
    fallback = settings.book_config()["cover"]["fallback"]
    assert out == assets / fallback
    assert fallback == "alyasmeen.png"


def test_assemble_embeds_cover_when_present(assets, ds, monkeypatch):
    cover_name = settings.book_config()["paths"]["cover"]
    (assets / cover_name).write_bytes(_PNG)

    block = assemble.deterministic_block(ds)

    # (d) deterministic_block embeds the generated cover by bare filename
    assert f"![אליאסמין]({cover_name})" in block


def test_bundled_fallback_is_committed():
    fallback = settings.book_config()["cover"]["fallback"]
    real = Path(settings.package_dir()) / "assets" / fallback
    assert real.exists() and real.stat().st_size > 0


def test_env_example_lists_all_phase_keys():
    for parent in Path(settings.package_dir()).parents:
        env = parent / ".env-example"
        if env.exists():
            text = env.read_text()
            for env_name in load_llm_config()["key_envs"].values():
                assert env_name in text
            return
    pytest.fail("no .env-example found")
