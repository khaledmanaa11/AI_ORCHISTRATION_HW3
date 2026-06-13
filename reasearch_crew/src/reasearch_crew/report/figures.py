from __future__ import annotations

from urllib.parse import urlparse

from .dataset import Dataset
from .economics import equations

# Market-sizing equations plotted as the funnel bar chart.
_FUNNEL = ("TAM", "SAM", "SOM")


def _domain(url: str) -> str:
    """The bare domain of a source URL — short enough to fit the table column."""
    net = urlparse(url).netloc or url
    return net[4:] if net.startswith("www.") else net


def _row(label: str, value: float, unit: str, source: str) -> str:
    return (
        rf"\textbf{{{label}}} & {value:,.2f} & {unit} & "
        rf"\href{{{source}}}{{\footnotesize {_domain(source)}}} \\"
    )


def table_snippet(ds: Dataset) -> str:
    """A zebra-striped, teal-headed table — one row per validated figure."""
    body = "\n".join(
        _row(f.label or f.name, f.value, f.unit, f.source) for f in ds.figures
    )
    return (
        "{\\rowcolors{2}{brandtint}{white}%\n"
        "\\arrayrulecolor{brandteal}\\setlength{\\arrayrulewidth}{0.8pt}%\n"
        "\\renewcommand{\\arraystretch}{1.35}%\n"
        "\\begin{tabularx}{\\linewidth}{@{}X r l l@{}}\n"
        "\\rowcolor{brandteal}\n"
        "\\textcolor{white}{\\textbf{מדד}} & "
        "\\textcolor{white}{\\textbf{ערך}} & "
        "\\textcolor{white}{\\textbf{יחידה}} & "
        "\\textcolor{white}{\\textbf{מקור}} \\\\\n"
        f"{body}\n"
        "\\bottomrule\n"
        "\\end{tabularx}}"
    )


def funnel_values(ds: Dataset) -> list[tuple[str, float]]:
    """The (label, value) pairs the graph plots — the market-sizing funnel."""
    eqs = {e.name: e for e in equations(ds)}
    return [(name, eqs[name].value) for name in _FUNNEL]


def graph_snippet(ds: Dataset) -> str:
    """A branded pgfplots bar chart of the TAM→SAM→SOM funnel, in USD."""
    pairs = funnel_values(ds)
    coords = " ".join(f"({label},{value:.0f})" for label, value in pairs)
    symbolic = ",".join(label for label, _ in pairs)
    return (
        "\\begin{tikzpicture}\n"
        "\\begin{axis}[\n"
        "  width=0.92\\linewidth, height=6.4cm,\n"
        "  ybar, bar width=1.15cm, ymin=0, enlarge x limits=0.32,\n"
        "  axis lines=left, axis line style={brandteal!40},\n"
        "  ymajorgrids, grid style={brandteal!12},\n"
        "  ylabel={USD}, ylabel style={font=\\small\\bfseries, brandteal},\n"
        "  scaled y ticks=base 10:-9, ytick scale label code/.code={},\n"
        "  yticklabel style={font=\\footnotesize, brandteal!80},\n"
        f"  symbolic x coords={{{symbolic}}}, xtick=data,\n"
        "  xticklabel style={font=\\bfseries, brandteal},\n"
        "  nodes near coords, every node near coord/.append style={\n"
        "    font=\\footnotesize\\bfseries, brandteal,\n"
        "    /pgf/number format/.cd, fixed, precision=0,\n"
        "    set thousands separator={,}},\n"
        "]\n"
        "\\addplot[ybar, fill=brandteal, draw=brandgold, line width=0.9pt,\n"
        f"  rounded corners=1.5pt] coordinates {{{coords}}};\n"
        "\\end{axis}\n"
        "\\end{tikzpicture}"
    )


def _human_usd(value: float) -> str:
    """A compact human label for a USD figure ($14.9B, $5.96B, $119M)."""
    if value >= 1e9:
        return f"\\${value / 1e9:.2f}B"
    if value >= 1e6:
        return f"\\${value / 1e6:.0f}M"
    if value >= 1e3:
        return f"\\${value / 1e3:.0f}K"
    return f"\\${value:,.0f}"


def kpi_cards(ds: Dataset) -> str:
    """Three brand KPI cards (TAM / SAM / SOM) rendered via the \\kpicard macro."""
    eqs = {e.name: e for e in equations(ds)}
    cards = [
        f"\\kpicard{{{name}}}{{{_human_usd(eqs[name].value)}}}"
        for name in _FUNNEL
    ]
    return (
        "\\begin{center}\n\\setlength{\\tabcolsep}{6pt}\n"
        "\\begin{tabular}{ccc}\n"
        + " &\n".join(cards)
        + "\n\\end{tabular}\n\\end{center}"
    )
