from pathlib import Path
from types import SimpleNamespace

import pytest

from reasearch_crew.gateway import telemetry
from reasearch_crew.gateway import rate_limiter
from reasearch_crew.report import compile as compile_mod
from reasearch_crew.report import render as render_mod

_RESEARCH_MD = """# מחקר שוק אליאסמין

ממצאים עם מקורות.

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


def _fake_subprocess(argv, capture_output=False, text=False, **kwargs):
    """Stand in for pandoc/xelatex: actually create the output artifact."""
    if any(a.startswith("-jobname=") for a in argv):  # xelatex / lualatex
        outdir = next(
            a.split("=", 1)[1] for a in argv if a.startswith("-output-directory=")
        )
        job = next(a.split("=", 1)[1] for a in argv if a.startswith("-jobname="))
        Path(outdir, f"{job}.pdf").write_bytes(b"%PDF-1.5\n")
    else:  # pandoc
        target = argv[argv.index("-o") + 1]
        Path(target).write_text("% generated tex\n", encoding="utf-8")
    return SimpleNamespace(returncode=0, stdout="", stderr="")


@pytest.fixture(autouse=True)
def _reset():
    telemetry.reset()
    rate_limiter.reset()
    yield
    telemetry.reset()
    rate_limiter.reset()


def test_full_chain(api_key, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)

    from crewai import LLM
    from crewai.agent import Agent

    monkeypatch.setattr(
        LLM,
        "call",
        lambda self, *a, **k: {
            "choices": [{"message": "x"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        },
    )
    monkeypatch.setattr(render_mod.subprocess, "run", _fake_subprocess)
    monkeypatch.setattr(compile_mod.subprocess, "run", _fake_subprocess)

    def fake_execute(self, task, context=None, tools=None):
        self.llm.call([{"role": "user", "content": "x"}])  # bank some tokens
        if "Research" in self.role:
            return _RESEARCH_MD
        from reasearch_crew.tools.typeset import render_and_compile

        return render_and_compile()

    monkeypatch.setattr(Agent, "execute_task", fake_execute)

    from reasearch_crew.main import run

    run()

    out = tmp_path / "output"
    for artifact in (
        "research.md",
        "data.json",
        "book.he.md",
        "book.he.tex",
        "book.pdf",
    ):
        assert (out / artifact).exists(), f"missing {artifact}"

    # flush() reported token totals for the Gemini provider (§11).
    # researcher(10) + 12 compose sections × 10 + typesetter(10) = 140
    printed = capsys.readouterr().out
    assert "gateway[gemini]" in printed
    assert "in_tokens=140" in printed
