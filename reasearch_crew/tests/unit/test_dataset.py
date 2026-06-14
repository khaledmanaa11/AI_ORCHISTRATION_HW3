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


_JSON_TAGGED = """Thought: here is my brief.

```json
[
  {"name": "tam", "label": "TAM", "value": 8200000000, "unit": "USD",
   "source": "https://dataintelo.example/tam"},
  {"name": "churn", "label": "Churn", "value": 0.04, "unit": "decimal",
   "source": "https://churnkey.example/churn"}
]
```
"""

_UNTAGGED = (
    "prose\n\n```\n[{\"name\": \"tam\", \"value\": 1, \"unit\": \"USD\", "
    '"source": "https://s"}]\n```'
)

_DECOY_THEN_FIGURES = """A config sample:

```json
{"model": "gemini", "rpm": 5}
```

and the figures:

```json
[{"name": "arpu", "value": 0.26, "unit": "USD", "source": "https://s"}]
```
"""


def test_json_tagged_block_parses():
    """The live Researcher tags the array ```json, not ```figures."""
    figs = parse_figures(_JSON_TAGGED)
    assert [f.name for f in figs] == ["tam", "churn"]
    assert figs[0].value == 8200000000.0


def test_untagged_fence_parses():
    figs = parse_figures(_UNTAGGED)
    assert figs[0].name == "tam"


def test_non_figure_json_object_is_skipped():
    """A decoy ```json object must not shadow the real figures array."""
    figs = parse_figures(_DECOY_THEN_FIGURES)
    assert len(figs) == 1
    assert figs[0].name == "arpu"


# The live Researcher opened ```markdown and ```json but never closed either,
# so the payload ends at ']' with no trailing fence — the D15 crash.
_UNCLOSED_FENCE = (
    "```markdown\nprose about the market.\n\n```json\n[\n"
    '  {"name": "tam", "value": 45000000000, "unit": "USD",\n'
    '   "source": "https://e.example"},\n'
    '  {"name": "arpu", "value": 79, "unit": "USD",\n'
    '   "source": "https://f.example"}\n]'
)


def test_unclosed_fence_parses():
    """An unclosed ```json fence (payload ending at ']') must still parse."""
    figs = parse_figures(_UNCLOSED_FENCE)
    assert [f.name for f in figs] == ["tam", "arpu"]
    assert figs[0].value == 45000000000.0
