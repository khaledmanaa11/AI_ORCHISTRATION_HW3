from __future__ import annotations

from pathlib import Path

from reasearch_crew import settings
from reasearch_crew.report.outline import section_outline

# Hebrew prose guardrails echoing tasks.yaml writing_task constraints.
_GUARD = (
    "כתוב פרוזה זורמת בלבד — ללא טבלאות, גרפים, בלוקי JSON, "
    "קוד (```) , LaTeX, תמונות, או כותרת ראשית (#). "
    "התחל ישירות בפסקה הראשונה של הסעיף, ללא כותרת חוזרת."
)


def _section_prompt(section: str, research_brief: str, min_words: int) -> str:
    return (
        f"כתוב את הסעיף '{section}' לספר מחקר שוק בעברית.\n\n"
        f"תקציר המחקר:\n{research_brief}\n\n"
        f"{_GUARD}\n\n"
        f"כתוב לפחות {min_words} מילים בסעיף זה."
    )


def _extract_text(response) -> str:
    """Pull prose text from a GatekeptLLM.call response."""
    if isinstance(response, str):
        return response
    if isinstance(response, dict):
        choices = response.get("choices", [])
        if choices:
            msg = choices[0].get("message", "")
            if isinstance(msg, dict):
                return msg.get("content", str(msg))
            return str(msg)
    return str(response)


def compose_book(llm, research_brief: str, book_md: Path) -> None:
    """Write the Hebrew book section-by-section to avoid per-call token ceiling.

    Each section is a separate GatekeptLLM.call so total length scales past
    the output-token truncation limit (ADR-D6).
    """
    cfg = settings.book_config()
    words_per_page: int = cfg["words_per_page"]
    pages_per_section: int = cfg.get("pages_per_section", 3)
    min_words = words_per_page * pages_per_section
    sections = section_outline()

    book_md = Path(book_md)
    book_md.parent.mkdir(parents=True, exist_ok=True)
    book_md.write_text("", encoding="utf-8")

    with book_md.open("a", encoding="utf-8") as fh:
        for section in sections:
            prompt = _section_prompt(section, research_brief, min_words)
            response = llm.call([{"role": "user", "content": prompt}])
            text = _extract_text(response)
            fh.write(f"## {section}\n\n{text}\n\n")
