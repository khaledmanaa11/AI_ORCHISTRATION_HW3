from __future__ import annotations

from .dataset import Dataset
from .economics import equations

# Market-sizing equations plotted as the funnel bar chart.
_FUNNEL = ("TAM", "SAM", "SOM")


def _row(label: str, value: float, unit: str, source: str) -> str:
    return rf"{label} & {value:,.2f} & {unit} & \url{{{source}}} \\"


def table_snippet(ds: Dataset) -> str:
    """A booktabs table — one row per validated figure (label/value/unit/source)."""
    body = "\n".join(
        _row(f.label or f.name, f.value, f.unit, f.source) for f in ds.figures
    )
    return (
        "\\begin{tabular}{llll}\n"
        "\\toprule\n"
        "מדד & ערך & יחידה "
        "& מקור \\\\\n"
        "\\midrule\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabular}"
    )


def funnel_values(ds: Dataset) -> list[tuple[str, float]]:
    """The (label, value) pairs the graph plots — the market-sizing funnel."""
    eqs = {e.name: e for e in equations(ds)}
    return [(name, eqs[name].value) for name in _FUNNEL]


def graph_snippet(ds: Dataset) -> str:
    """A pgfplots bar chart of the TAM→SAM→SOM funnel, in USD."""
    pairs = funnel_values(ds)
    coords = " ".join(f"({label},{value:.0f})" for label, value in pairs)
    symbolic = ",".join(label for label, _ in pairs)
    return (
        "\\begin{tikzpicture}\n"
        "\\begin{axis}[\n"
        "  ybar, ymin=0, ylabel={USD},\n"
        f"  symbolic x coords={{{symbolic}}},\n"
        "  xtick=data, nodes near coords,\n"
        "]\n"
        f"\\addplot coordinates {{{coords}}};\n"
        "\\end{axis}\n"
        "\\end{tikzpicture}"
    )
