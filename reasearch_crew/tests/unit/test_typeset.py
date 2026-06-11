from types import SimpleNamespace

from reasearch_crew.report import compile as compile_mod
from reasearch_crew.report import render as render_mod
from reasearch_crew.tools import typeset

_RESEARCH = """# מחקר

```figures
[
  {"name": "tam", "label": "TAM", "value": 1200000000, "unit": "USD",
   "source": "https://s/tam"},
  {"name": "sam_share", "value": 0.25, "unit": "ratio", "source": "https://s/1"},
  {"name": "som_share", "value": 0.10, "unit": "ratio", "source": "https://s/2"},
  {"name": "arpu", "value": 20, "unit": "USD/mo", "source": "https://s/3"},
  {"name": "gross_margin", "value": 0.8, "unit": "ratio", "source": "https://s/4"},
  {"name": "churn", "value": 0.05, "unit": "/mo", "source": "https://s/5"},
  {"name": "marketing_spend", "value": 50000, "unit": "USD", "source": "https://s/6"},
  {"name": "customers_acquired", "value": 500, "unit": "n", "source": "https://s/7"}
]
```
"""


def test_typesetter_has_render_and_compile_tool(api_key):
    from reasearch_crew.crew import ReasearchCrew

    crew_obj = ReasearchCrew().crew()
    typesetter = next(a for a in crew_obj.agents if "Typesetter" in a.role)
    assert "render_and_compile" in [t.name for t in typesetter.tools]


def test_render_and_compile_orchestrates_chain(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "research.md").write_text(_RESEARCH, encoding="utf-8")
    (tmp_path / "output" / "book.he.md").write_text(
        "# הספר\n\nתקציר.\n", encoding="utf-8"
    )

    # pandoc + xelatex are local subprocesses — mock both.
    monkeypatch.setattr(
        render_mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        compile_mod.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    out = typeset.render_and_compile()

    assert out.endswith("book.pdf")
    assert (tmp_path / "output" / "data.json").exists()
    book_md = (tmp_path / "output" / "book.he.md").read_text(encoding="utf-8")
    assert "tikzpicture" in book_md   # graph injected
    assert "tabular" in book_md       # table injected
    assert "mathrm{LTV}" in book_md   # equations injected
