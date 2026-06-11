from __future__ import annotations

import subprocess
from pathlib import Path

from reasearch_crew import settings

from .errors import TypesetError


def markdown_to_latex(md: Path, tex: Path, *, template: Path) -> Path:
    """Convert Hebrew markdown to a .tex via pandoc, using the book template.

    The pandoc binary is taken from book.json.bin.pandoc (absolute path or bare
    name) — never assumed on PATH (§7.2). The Hebrew font, title, author and
    asset directory are injected as template variables from book.json. Raises
    TypesetError on a non-zero exit.
    """
    cfg = settings.book_config()
    argv = [
        cfg["bin"]["pandoc"],
        str(md),
        "-o",
        str(tex),
        "--standalone",
        "--template",
        str(template),
        f"--pdf-engine={cfg['pdf_engine']}",
        "-V",
        f"hebrewfont={cfg['hebrew_font']}",
        "-V",
        f"assetdir={settings.asset_dir().as_posix()}",
        "-V",
        f"title={cfg['title']}",
        "-V",
        f"author={cfg['author']}",
    ]
    proc = subprocess.run(argv, capture_output=True, text=True)
    if proc.returncode != 0:
        raise TypesetError(f"pandoc failed ({proc.returncode}): {proc.stderr}")
    return Path(tex)
