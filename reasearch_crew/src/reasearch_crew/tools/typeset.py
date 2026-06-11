from __future__ import annotations

from pathlib import Path

from crewai.tools import tool

from reasearch_crew import settings
from reasearch_crew.report.assemble import assemble_markdown
from reasearch_crew.report.compile import compile_pdf
from reasearch_crew.report.dataset import load_dataset, read_dataset
from reasearch_crew.report.render import markdown_to_latex


def render_and_compile() -> str:
    """research.md → data.json → book.he.md (+ table/graph/eqs) → .tex → .pdf.

    The deterministic artifacts are injected here, not by the LLM (ADR-D2).
    pandoc and xelatex are local subprocesses, resolved from book.json.bin.
    """
    paths = settings.book_config()["paths"]
    data_json = load_dataset(Path(paths["research_md"]), Path(paths["data_json"]))
    ds = read_dataset(data_json)
    book_md = assemble_markdown(Path(paths["book_md"]), ds)
    tex = markdown_to_latex(
        book_md, Path(paths["book_tex"]), template=settings.template_path()
    )
    return str(compile_pdf(tex))


@tool("render_and_compile")
def render_and_compile_tool() -> str:
    """Build output/data.json from research.md, weave the table, graph, figure
    and equations into the Hebrew book markdown, convert it to LaTeX with the
    XeLaTeX template and compile the final PDF. Returns the path to book.pdf."""
    return render_and_compile()
