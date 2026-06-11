import pytest

from reasearch_crew.report.dataset import (
    Dataset,
    DatasetError,
    load_dataset,
    parse_figures,
    read_dataset,
)

_SOURCED = """# Research

Some prose about the market.

```figures
[
  {"name": "tam", "label": "TAM", "value": 1200000000, "unit": "USD",
   "source": "https://statista.example/tam"},
  {"name": "arpu", "label": "ARPU", "value": 18.5, "unit": "USD/mo",
   "source": "https://report.example/arpu"}
]
```
"""

_SOURCELESS = """```figures
[{"name": "tam", "value": 1200000000, "unit": "USD"}]
```"""


def test_sourced_figure_parses():
    figs = parse_figures(_SOURCED)
    assert len(figs) == 2
    assert figs[0].name == "tam"
    assert figs[0].value == 1200000000.0
    assert figs[0].source.startswith("https://")


def test_sourceless_figure_raises():
    with pytest.raises(DatasetError, match="source"):
        parse_figures(_SOURCELESS)


def test_missing_block_raises():
    with pytest.raises(DatasetError, match="figures block"):
        parse_figures("# no figures here")


def test_round_trips_through_data_json(tmp_path):
    research = tmp_path / "research.md"
    research.write_text(_SOURCED, encoding="utf-8")
    data_json = tmp_path / "output" / "data.json"

    out = load_dataset(research, data_json)
    assert out == data_json
    assert data_json.exists()

    ds = read_dataset(data_json)
    assert isinstance(ds, Dataset)
    assert ds.value("arpu") == 18.5
    assert ds.by_name("tam").unit == "USD"
    assert "https://report.example/arpu" in ds.sources()


def test_unknown_name_raises(tmp_path):
    research = tmp_path / "research.md"
    research.write_text(_SOURCED, encoding="utf-8")
    ds = read_dataset(load_dataset(research, tmp_path / "data.json"))
    with pytest.raises(KeyError):
        ds.by_name("nope")


def test_malformed_json_raises():
    with pytest.raises(DatasetError, match="valid JSON"):
        parse_figures("```figures\n[not json,]\n```")


def test_empty_array_raises():
    with pytest.raises(DatasetError, match="non-empty"):
        parse_figures("```figures\n[]\n```")


def test_zero_value_is_allowed():
    block = (
        '```figures\n[{"name": "x", "value": 0, "unit": "u", '
        '"source": "https://s"}]\n```'
    )
    assert parse_figures(block)[0].value == 0.0
