from types import SimpleNamespace

import pytest

from reasearch_crew import settings
from reasearch_crew.report import compile as compile_mod
from reasearch_crew.report.errors import TypesetError


def _capture(monkeypatch, returncode=0, stderr=""):
    calls = []

    def fake_run(argv, capture_output=False, text=False):
        calls.append(argv)
        return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)

    monkeypatch.setattr(compile_mod.subprocess, "run", fake_run)
    return calls


def test_engine_argv_and_pdf_path(monkeypatch, tmp_path):
    calls = _capture(monkeypatch)
    pdf = compile_mod.compile_pdf(tmp_path / "book.he.tex")

    argv = calls[0]
    assert argv[0] == settings.book_config()["bin"]["xelatex"]
    assert str(tmp_path / "book.he.tex") in argv
    assert any(a.startswith("-jobname=book") for a in argv)
    assert pdf.name == "book.pdf"


def test_runs_twice_for_pgfplots(monkeypatch, tmp_path):
    calls = _capture(monkeypatch)
    compile_mod.compile_pdf(tmp_path / "book.he.tex")
    assert len(calls) == 2


def test_nonzero_exit_raises(monkeypatch, tmp_path):
    _capture(monkeypatch, returncode=1, stderr="LaTeX error")
    with pytest.raises(TypesetError, match="xelatex failed"):
        compile_mod.compile_pdf(tmp_path / "book.he.tex")
