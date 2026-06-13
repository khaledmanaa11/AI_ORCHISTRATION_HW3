from __future__ import annotations

import base64
from pathlib import Path

from reasearch_crew import settings
from reasearch_crew.gateway import GatewayError, http_post, resolve_key

_MODEL_SLOT = "<model>"


def _prompt(cfg: dict) -> str:
    """Build the image prompt from book.json's title/topic (no literal in .py)."""
    return cfg["cover"]["prompt_template"].format(
        title=cfg["title"], topic=cfg["topic"]
    )


def _fallback() -> Path:
    """The bundled ALYASMEEN raster — used whenever generation can't run."""
    return settings.asset_dir() / settings.book_config()["cover"]["fallback"]


def generate_cover() -> Path:
    """Generate the ALYASMEEN cover through the gateway image seam (§5.1).

    A missing typeset-phase credential skips the call and returns the bundled
    image. Gateway, decode, or response-shape failures also degrade safely.
    """
    _, key = resolve_key("typeset", required=False)
    if not key:
        return _fallback()

    cfg = settings.book_config()
    cover = cfg["cover"]
    url = settings.endpoint("gemini_image").replace(_MODEL_SLOT, cover["model"])
    try:
        data = http_post(
            url,
            headers={
                "x-goog-api-key": key,
                "Content-Type": "application/json",
            },
            json={
                "instances": [{"prompt": _prompt(cfg)}],
                "parameters": {"sampleCount": 1},
            },
            provider="gemini_image",
            timeout=cover["timeout"],
        )
        raw = base64.b64decode(data["predictions"][0]["bytesBase64Encoded"])
    except (GatewayError, KeyError, IndexError, TypeError, ValueError):
        return _fallback()

    dest = settings.asset_dir() / cfg["paths"]["cover"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(raw)
    return dest
