"""Smoke test: full run() pipeline produces book.he.md with Hebrew headings."""
import base64
from pathlib import Path
from types import SimpleNamespace

from crewai import LLM
from crewai.agent import Agent

from reasearch_crew import settings
from reasearch_crew.gateway import rate_limiter, telemetry
from reasearch_crew.report import compile as compile_mod
from reasearch_crew.report import cover as cover_mod
from reasearch_crew.report import render as render_mod

_PNG = b"\x89PNG\r\n\x1a\n-fake-cover"
_RESEARCH_MD = """# מחקר שוק
ממצאים.

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


def _fake_sub(argv, capture_output=False, text=False, **kwargs):
    if any(a.startswith("-jobname=") for a in argv):
        outdir = next(a.split("=", 1)[1] for a in argv if a.startswith("-output-directory="))
        job = next(a.split("=", 1)[1] for a in argv if a.startswith("-jobname="))
        Path(outdir, f"{job}.pdf").write_bytes(b"%PDF-1.5\n")
    else:
        Path(argv[argv.index("-o") + 1]).write_text("% tex\n", encoding="utf-8")
    return SimpleNamespace(returncode=0, stdout="", stderr="")


def test_paper_written_to_output_dir(api_key, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(rate_limiter.time, "sleep", lambda seconds: None)
    assets = tmp_path / "assets"
    assets.mkdir()
    monkeypatch.setattr(settings, "asset_dir", lambda: assets)
    monkeypatch.setattr(
        cover_mod,
        "http_post",
        lambda *a, **k: {
            "predictions": [{
                "bytesBase64Encoded": base64.b64encode(_PNG).decode()
            }]
        },
    )

    monkeypatch.setattr(
        LLM,
        "call",
        lambda self, *a, **k: {
            "choices": [{"message": {"content": "פרוזה בדויה"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10},
        },
    )
    monkeypatch.setattr(render_mod.subprocess, "run", _fake_sub)
    monkeypatch.setattr(compile_mod.subprocess, "run", _fake_sub)

    def fake_execute(self, task, context=None, tools=None):
        self.llm.call([{"role": "user", "content": "x"}])
        if "Research" in self.role:
            return _RESEARCH_MD
        from reasearch_crew.tools.typeset import render_and_compile
        return render_and_compile()

    monkeypatch.setattr(Agent, "execute_task", fake_execute)

    telemetry.reset()
    rate_limiter.reset()

    from reasearch_crew.main import run
    run()

    book = tmp_path / "output" / "book.he.md"
    assert book.exists(), f"missing book.he.md; contents: {list((tmp_path / 'output').iterdir())}"
    content = book.read_text(encoding="utf-8")
    # compose_book writes one ## heading per section
    assert "## " in content

    telemetry.reset()
    rate_limiter.reset()
