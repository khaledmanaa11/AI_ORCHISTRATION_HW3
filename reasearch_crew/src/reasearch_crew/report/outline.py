from __future__ import annotations

import math

from reasearch_crew import settings

# Base Hebrew section outline for the ALYASMEEN market-research book.
_BASE_SECTIONS = (
    "תקציר מנהלים",
    "מבוא: השוק של אליאסמין",
    "סקירת השוק והמגמות",
    "גודל השוק: TAM, SAM, SOM",
    "קהל היעד והפרסונות",
    "הנוף התחרותי",
    "כלכלת היחידה: ARPU, נטישה, CAC, LTV",
    "אסטרטגיית הגעה לשוק",
    "תמחור ומודל הכנסות",
    "סיכונים והפחתתם",
    "מפת דרכים",
    "סיכום ומסקנות",
)


def section_outline(
    page_target: int | None = None,
    pages_per_section: int | None = None,
) -> list[str]:
    """Hebrew section titles sized so the book reaches `page_target` (ADR-D6).

    Defaults come from book.json. The Author writes each section in turn and
    appends it, so length scales without hitting output-token truncation.
    """
    cfg = settings.book_config()
    page_target = page_target or cfg["page_target"]
    pages_per_section = pages_per_section or cfg.get("pages_per_section", 3)
    needed = math.ceil(page_target / pages_per_section)

    sections = list(_BASE_SECTIONS)
    extra = 1
    while len(sections) < needed:
        sections.append(f"ניתוח מעמיק {extra}")
        extra += 1
    return sections
