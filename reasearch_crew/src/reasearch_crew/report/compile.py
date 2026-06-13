from __future__ import annotations

import subprocess
from pathlib import Path

from reasearch_crew import settings

from .errors import TypesetError


def compile_pdf(tex: Path) -> Path:
    """Compile a .tex to a PDF with the configured XeLaTeX engine.

    The engine comes from book.json.bin.xelatex (path or bare name, never
    assumed on PATH, §7.2). The output is named after book.json.paths.book_pdf
    via -jobname, so book.he.tex still yields book.pdf. Runs twice so pgfplots
    and cross-references resolve. A non-zero exit raises TypesetError.
    """
    cfg = settings.book_config()
    tex = Path(tex)
    jobname = Path(cfg["paths"]["book_pdf"]).stem
    outdir = tex.parent
    argv = [
        cfg["bin"]["xelatex"],
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-output-directory={outdir}",
        f"-jobname={jobname}",
        str(tex),
    ]
    for _ in range(2):
        proc = subprocess.run(
            argv, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            raise TypesetError(
                f"xelatex failed ({proc.returncode}):\n"
                f"STDERR: {(proc.stderr or '')[-500:]}\n"
                f"STDOUT: {(proc.stdout or '')[-1500:]}"
            )
    return outdir / f"{jobname}.pdf"
