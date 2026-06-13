from __future__ import annotations

from pathlib import Path

from reasearch_crew import settings

from .dataset import Dataset
from .economics import equations
from .figures import graph_snippet, kpi_cards, table_snippet
from .sanitize import clean_narrative


def _asset_name() -> str:
    images = sorted(p.name for p in settings.asset_dir().glob("*.png"))
    return images[0] if images else ""


def _cover_name() -> str:
    """The AI-generated cover (paths.cover) if it landed, else the first PNG."""
    cover = settings.book_config()["paths"].get("cover")
    if cover and (settings.asset_dir() / cover).exists():
        return cover
    return _asset_name()


def _equation_panel(ds: Dataset) -> str:
    """Every proved equation, aligned inside the branded eqbox panel."""
    rows = " \\\\[4pt]\n".join(
        e.latex.replace("= ", "&= ", 1) for e in equations(ds)
    )
    return (
        "\\begin{eqbox}\n\\begin{align*}\n"
        f"{rows}\n"
        "\\end{align*}\n\\end{eqbox}"
    )


def _latex(snippet: str) -> list[str]:
    return ["```{=latex}", snippet, "```", ""]


def deterministic_block(ds: Dataset) -> str:
    """The data dashboard — KPI cards, table, chart, equations and the logo,
    all built from data.json, not the LLM (ADR-D2), wrapped as raw LaTeX so
    they pass straight through pandoc."""
    image = _cover_name()
    parts = [
        *_latex("\\clearpage"),
        "# לוח נתונים — גודל השוק של אליאסמין",
        "",
        *_latex(kpi_cards(ds)),
        "## טבלת מדדי השוק",
        "",
        *_latex(table_snippet(ds)),
        "## תרשים: משפך גודל השוק (TAM → SAM → SOM)",
        "",
        *_latex(graph_snippet(ds)),
        "## משוואות מפתח",
        "",
        *_latex(_equation_panel(ds)),
    ]
    if image:
        parts += ["## הזהות", "", f"![אליאסמין]({image})"]
    return "\n".join(parts)


def assemble_markdown(book_md: Path, ds: Dataset) -> Path:
    """Sanitise the Author's prose, then append the deterministic dashboard."""
    book_md = Path(book_md)
    raw = book_md.read_text(encoding="utf-8") if book_md.exists() else ""
    narrative = clean_narrative(raw)
    book_md.parent.mkdir(parents=True, exist_ok=True)
    book_md.write_text(
        narrative + "\n" + deterministic_block(ds), encoding="utf-8"
    )
    return book_md
