from __future__ import annotations

from pathlib import Path

from reasearch_crew import settings

from .dataset import Dataset
from .economics import equations
from .figures import graph_snippet, table_snippet


def _asset_name() -> str:
    images = sorted(p.name for p in settings.asset_dir().glob("*.png"))
    return images[0] if images else ""


def deterministic_block(ds: Dataset) -> str:
    """The table, graph, figure and equations — built from data.json, not the
    LLM (ADR-D2). Wrapped as pandoc raw-LaTeX so they pass straight through."""
    eq_tex = "\n\n".join(rf"\[{e.latex}\]" for e in equations(ds))
    image = _asset_name()
    parts = [
        "## נתוני שוק",
        "",
        "```{=latex}",
        table_snippet(ds),
        "```",
        "",
        "## תרשים גודל השוק",
        "",
        "```{=latex}",
        graph_snippet(ds),
        "```",
        "",
        "## תמונה",
        "",
        f"![אליאסמין]({image})" if image else "",
        "",
        "## משוואות",
        "",
        "```{=latex}",
        eq_tex,
        "```",
    ]
    return "\n".join(parts)


def assemble_markdown(book_md: Path, ds: Dataset) -> Path:
    """Append the deterministic block to the Author's Hebrew markdown in place."""
    book_md = Path(book_md)
    text = book_md.read_text(encoding="utf-8") if book_md.exists() else ""
    book_md.parent.mkdir(parents=True, exist_ok=True)
    book_md.write_text(
        text + "\n\n" + deterministic_block(ds), encoding="utf-8"
    )
    return book_md
