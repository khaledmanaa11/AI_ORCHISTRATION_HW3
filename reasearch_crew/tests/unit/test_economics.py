import pytest

from reasearch_crew.report.dataset import Dataset, Figure
from reasearch_crew.report.economics import equations


def _fig(name, value, unit="x"):
    return Figure(name=name, value=value, unit=unit, source="https://s")


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


def test_market_sizing_matches_fixture(ds):
    eq = {e.name: e for e in equations(ds)}
    assert eq["TAM"].value == 1_200_000_000
    assert eq["SAM"].value == pytest.approx(300_000_000)  # 1.2e9 * 0.25
    assert eq["SOM"].value == pytest.approx(30_000_000)   # 300e6 * 0.10


def test_unit_economics_matches_fixture(ds):
    eq = {e.name: e for e in equations(ds)}
    assert eq["LTV"].value == pytest.approx(320.0)     # 20*0.8/0.05
    assert eq["CAC"].value == pytest.approx(100.0)     # 50000/500
    assert eq["Payback"].value == pytest.approx(6.25)  # 100/(20*0.8)


def test_every_equation_has_nonempty_latex(ds):
    eqs = equations(ds)
    assert len(eqs) == 6
    for e in eqs:
        assert e.latex.strip()
        assert "\\" in e.latex


def test_units_carried(ds):
    eq = {e.name: e for e in equations(ds)}
    assert eq["Payback"].unit == "months"
    assert eq["LTV"].unit == "USD"
