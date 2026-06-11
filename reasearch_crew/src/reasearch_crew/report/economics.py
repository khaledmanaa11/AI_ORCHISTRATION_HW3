from __future__ import annotations

from dataclasses import dataclass

from .dataset import Dataset

# Figure names the equation set expects in data.json.
REQUIRED_FIGURES = (
    "tam",
    "sam_share",
    "som_share",
    "arpu",
    "gross_margin",
    "churn",
    "marketing_spend",
    "customers_acquired",
)


@dataclass(frozen=True)
class Equation:
    name: str
    latex: str
    value: float
    unit: str = ""


def _money(value: float) -> str:
    return f"{value:,.0f}"


def equations(ds: Dataset) -> list[Equation]:
    """The report's proved equation set, each LaTeX + numeric, from `ds`.

    Market sizing (TAM→SAM→SOM) and unit economics (LTV, CAC, payback). Every
    number is pulled from the validated dataset so the prose, table, graph and
    equations can never disagree (ADR-D5).
    """
    tam = ds.value("tam")
    sam_share = ds.value("sam_share")
    som_share = ds.value("som_share")
    arpu = ds.value("arpu")
    margin = ds.value("gross_margin")
    churn = ds.value("churn")
    spend = ds.value("marketing_spend")
    acquired = ds.value("customers_acquired")

    sam = tam * sam_share
    som = sam * som_share
    ltv = arpu * margin / churn
    cac = spend / acquired
    payback = cac / (arpu * margin)

    return [
        Equation(
            "TAM",
            rf"\mathrm{{TAM}} = {_money(tam)}\ \text{{USD}}",
            tam,
            "USD",
        ),
        Equation(
            "SAM",
            rf"\mathrm{{SAM}} = \mathrm{{TAM}}\times {sam_share:.2f}"
            rf" = {_money(sam)}\ \text{{USD}}",
            sam,
            "USD",
        ),
        Equation(
            "SOM",
            rf"\mathrm{{SOM}} = \mathrm{{SAM}}\times {som_share:.2f}"
            rf" = {_money(som)}\ \text{{USD}}",
            som,
            "USD",
        ),
        Equation(
            "LTV",
            rf"\mathrm{{LTV}} = \frac{{\mathrm{{ARPU}}\cdot m}}{{\mathrm{{churn}}}}"
            rf" = \frac{{{arpu:.2f}\cdot {margin:.2f}}}{{{churn:.3f}}}"
            rf" = {ltv:,.2f}\ \text{{USD}}",
            ltv,
            "USD",
        ),
        Equation(
            "CAC",
            rf"\mathrm{{CAC}} = \frac{{\text{{spend}}}}{{\text{{customers}}}}"
            rf" = \frac{{{_money(spend)}}}{{{_money(acquired)}}}"
            rf" = {cac:,.2f}\ \text{{USD}}",
            cac,
            "USD",
        ),
        Equation(
            "Payback",
            rf"t_{{\mathrm{{payback}}}} = \frac{{\mathrm{{CAC}}}}"
            rf"{{\mathrm{{ARPU}}\cdot m}}"
            rf" = {payback:,.2f}\ \text{{months}}",
            payback,
            "months",
        ),
    ]
