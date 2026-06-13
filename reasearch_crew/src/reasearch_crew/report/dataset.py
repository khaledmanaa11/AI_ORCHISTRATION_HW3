from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

_FIGURES_BLOCK = re.compile(r"```figures\s*(.+?)```", re.DOTALL)
_JSON_ARRAY = re.compile(r"```(?:json|figures)?\s*\n?(\[.*?\])\s*\n?```", re.DOTALL)
_REQUIRED = ("name", "value", "unit", "source")


class DatasetError(ValueError):
    """A figure is missing a required field or the block is unparsable."""


@dataclass(frozen=True)
class Figure:
    name: str
    value: float
    unit: str
    source: str
    label: str = ""


@dataclass(frozen=True)
class Dataset:
    figures: tuple[Figure, ...]

    def by_name(self, name: str) -> Figure:
        for fig in self.figures:
            if fig.name == name:
                return fig
        raise KeyError(f"no figure named {name!r}")

    def value(self, name: str) -> float:
        return self.by_name(name).value

    def sources(self) -> list[str]:
        return [f.source for f in self.figures]


def _validate(raw: dict) -> Figure:
    missing = [k for k in _REQUIRED if not raw.get(k) and raw.get(k) != 0]
    if missing:
        raise DatasetError(
            f"figure {raw.get('name', '?')!r} missing: {', '.join(missing)}"
        )
    return Figure(
        name=str(raw["name"]),
        value=float(raw["value"]),
        unit=str(raw["unit"]),
        source=str(raw["source"]),
        label=str(raw.get("label", "")),
    )


def _looks_like_figures(rows: object) -> bool:
    return (
        isinstance(rows, list)
        and bool(rows)
        and all(isinstance(r, dict) and "name" in r and "value" in r for r in rows)
    )


def _figures_block(text: str) -> str:
    """Find the figures JSON, tolerating ```figures / ```json / untagged fences.

    Live LLMs routinely tag the array ```json (or leave it bare) instead of the
    ```figures we ask for, so the deterministic tail must not depend on the tag.
    An explicit ```figures block still wins, preserving its strict error shape.
    """
    explicit = _FIGURES_BLOCK.search(text)
    if explicit:
        return explicit.group(1)
    for body in _JSON_ARRAY.findall(text):
        try:
            rows = json.loads(body)
        except json.JSONDecodeError:
            continue
        if _looks_like_figures(rows):
            return body
    raise DatasetError("no ```figures block found in research markdown")


def parse_figures(text: str) -> list[Figure]:
    """Pull the fenced figures JSON array out of research markdown."""
    block = _figures_block(text)
    try:
        rows = json.loads(block)
    except json.JSONDecodeError as exc:
        raise DatasetError(f"figures block is not valid JSON: {exc}") from exc
    if not isinstance(rows, list) or not rows:
        raise DatasetError("figures block must be a non-empty JSON array")
    return [_validate(row) for row in rows]


def load_dataset(research_md: Path, data_json: Path) -> Path:
    """Parse + validate research.md figures, write data.json, return its path."""
    figures = parse_figures(Path(research_md).read_text(encoding="utf-8"))
    data_json = Path(data_json)
    data_json.parent.mkdir(parents=True, exist_ok=True)
    payload = {"figures": [asdict(f) for f in figures]}
    data_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return data_json


def read_dataset(data_json: Path) -> Dataset:
    """Load a previously written data.json into a typed Dataset."""
    payload = json.loads(Path(data_json).read_text(encoding="utf-8"))
    return Dataset(figures=tuple(_validate(row) for row in payload["figures"]))
