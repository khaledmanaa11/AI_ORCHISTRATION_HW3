from __future__ import annotations

import json
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
_BOOK_PATH = _PKG_DIR / "config" / "book.json"
_cache: dict | None = None


def book_config(force: bool = False) -> dict:
    """Read config/book.json once and memoize. Pass force=True in tests."""
    global _cache
    if _cache is None or force:
        _cache = json.loads(_BOOK_PATH.read_text(encoding="utf-8"))
    return _cache


def package_dir() -> Path:
    """Absolute path to the installed package directory."""
    return _PKG_DIR


def asset_dir() -> Path:
    """Committed assets directory, resolved relative to the package."""
    return _PKG_DIR / book_config()["paths"]["assets"]


def template_path() -> Path:
    """The XeLaTeX template, resolved relative to the package."""
    return _PKG_DIR / book_config()["paths"]["template"]


def output_path(key: str) -> Path:
    """A cwd-relative output artifact path from book.json paths.<key>."""
    return Path(book_config()["paths"][key])


def reset_cache() -> None:
    global _cache
    _cache = None
