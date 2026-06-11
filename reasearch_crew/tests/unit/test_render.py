from pathlib import Path
from types import SimpleNamespace

import pytest

from reasearch_crew import settings
from reasearch_crew.report import render
from reasearch_crew.report.errors import TypesetError


def _capture(monkeypatch, returncode=0, stderr=""):
    seen = {}

    def fake_run(argv, capture_output=False, text=False):
        seen["argv"] = argv
        return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)

    monkeypatch.setattr(render.subprocess, "run", fake_run)
    return seen


def test_pandoc_argv(monkeypatch, tmp_path):
    seen = _capture(monkeypatch)
    template = tmp_path / "book.he.tex"
    out = render.markdown_to_latex(
        tmp_path / "book.he.md", tmp_path / "book.he.tex", template=template
    )
    argv = seen["argv"]
    assert argv[0] == settings.book_config()["bin"]["pandoc"]
    assert str(template) in argv
    assert "--pdf-engine=xelatex" in argv
    assert "--template" in argv
    assert out == Path(tmp_path / "book.he.tex")


def test_font_injected_from_config(monkeypatch, tmp_path):
    seen = _capture(monkeypatch)
    render.markdown_to_latex(
        tmp_path / "a.md", tmp_path / "a.tex", template=tmp_path / "t.tex"
    )
    font = settings.book_config()["hebrew_font"]
    assert f"hebrewfont={font}" in seen["argv"]


def test_nonzero_exit_raises(monkeypatch, tmp_path):
    _capture(monkeypatch, returncode=2, stderr="boom")
    with pytest.raises(TypesetError, match="pandoc failed"):
        render.markdown_to_latex(
            tmp_path / "a.md", tmp_path / "a.tex", template=tmp_path / "t.tex"
        )
