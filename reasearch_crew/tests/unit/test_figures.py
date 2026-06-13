import pytest

from reasearch_crew.report.dataset import Dataset, Figure
from reasearch_crew.report.figures import (
    _human_usd,
    funnel_values,
    graph_snippet,
    kpi_cards,
    table_snippet,
)


def _fig(name, value, unit="x", label=""):
    return Figure(name=name, value=value, unit=unit, source="https://s/x", label=label)


@pytest.fixture
def ds():
    return Dataset(
        figures=(
            _fig("tam", 1_200_000_000, "USD", "TAM"),
            _fig("sam_share", 0.25),
            _fig("som_share", 0.10),
            _fig("arpu", 20.0, "USD/mo"),
            _fig("gross_margin", 0.80),
            _fig("churn", 0.05, "/mo"),
            _fig("marketing_spend", 50_000, "USD"),
            _fig("customers_acquired", 500, "count"),
        )
    )


def _balanced(tex):
    return tex.count("\\begin{") == tex.count("\\end{") > 0


def test_table_has_a_row_per_figure_and_is_balanced(ds):
    tex = table_snippet(ds)
    assert _balanced(tex)
    assert tex.count("\\\\") >= len(ds.figures)
    assert "1,200,000,000.00" in tex  # TAM value rendered
    assert "\\href{https://s/x}" in tex  # source linked by domain


def test_graph_coordinates_equal_data_values(ds):
    # funnel: TAM=1.2e9, SAM=TAM*0.25=3e8, SOM=SAM*0.10=3e7
    assert funnel_values(ds) == [
        ("TAM", 1_200_000_000.0),
        ("SAM", 300_000_000.0),
        ("SOM", 30_000_000.0),
    ]
    tex = graph_snippet(ds)
    assert _balanced(tex)
    assert "(TAM,1200000000)" in tex
    assert "(SAM,300000000)" in tex
    assert "(SOM,30000000)" in tex


def test_graph_is_pgfplots(ds):
    tex = graph_snippet(ds)
    assert "\\begin{axis}" in tex
    assert "ybar" in tex


def test_human_usd_scales_by_magnitude():
    assert _human_usd(14_900_000_000) == "\\$14.90B"
    assert _human_usd(119_200_000) == "\\$119M"
    assert _human_usd(50_000) == "\\$50K"
    assert _human_usd(750) == "\\$750"


def test_kpi_cards_emit_one_card_per_funnel_stage(ds):
    tex = kpi_cards(ds)
    for stage in ("TAM", "SAM", "SOM"):
        assert f"\\kpicard{{{stage}}}" in tex
    assert tex.count("\\kpicard") == 3
