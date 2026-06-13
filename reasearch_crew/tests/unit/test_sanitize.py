from reasearch_crew.report.sanitize import clean_narrative


def test_drops_leaked_filename_heading():
    out = clean_narrative("# book.he.md\n\n## מבוא\n\nטקסט.\n")
    assert "book.he.md" not in out
    assert "# מבוא" in out
    assert "טקסט." in out


def test_drops_leaked_leading_title_h1():
    out = clean_narrative("# ALYASMEEN מחקר שוק\n\n## תקציר\n\nגוף.\n")
    assert "ALYASMEEN מחקר שוק" not in out
    assert out.lstrip().startswith("# תקציר")


def test_keeps_real_headings():
    out = clean_narrative("## תקציר מנהלים\n\nשורה.\n")
    assert "# תקציר מנהלים" in out


def test_strips_orphaned_figure_captions():
    text = (
        "## גודל\n\nפסקה.\n\n"
        "**טבלת 1: סיכום גודל השוק**\n\n"
        "**תרשים 1: גודל השוק (TAM, SAM, SOM)**\n\n"
        "פסקה אחרת.\n"
    )
    out = clean_narrative(text)
    assert "טבלת 1" not in out
    assert "תרשים 1" not in out
    assert "פסקה." in out and "פסקה אחרת." in out


def test_strips_see_figure_reference():
    out = clean_narrative("## א\n\nראו איור 1: דוגמה לפרסונות.\n\nהמשך.\n")
    assert "ראו איור" not in out
    assert "המשך." in out


def test_strips_leaked_table_and_graph_fences():
    text = (
        "## גודל השוק\n\nפסקה.\n\n"
        "```table\n| a | b |\n```\n\n"
        "```graph\n{\"type\": \"bar\"}\n```\n\n"
        "פסקה שנייה.\n"
    )
    out = clean_narrative(text)
    assert "type" not in out
    assert "| a | b |" not in out
    assert "פסקה." in out
    assert "פסקה שנייה." in out


def test_drops_empty_heading():
    out = clean_narrative("## א\n\nגוף.\n\n#\n\nעוד.\n")
    assert "\n#\n" not in "\n" + out + "\n"
    assert "גוף." in out and "עוד." in out


def test_strips_raw_latex_passthrough_fence():
    text = "## א\n\nגוף.\n\n```{=latex}\n\\clearpage\n```\n\nעוד.\n"
    out = clean_narrative(text)
    assert "clearpage" not in out
    assert "=latex" not in out
    assert "גוף." in out and "עוד." in out


def test_strips_json_and_latex_fences():
    text = "טקסט\n\n```json\n[1,2,3]\n```\n\n```latex\n\\foo\n```\nסוף\n"
    out = clean_narrative(text)
    assert "[1,2,3]" not in out
    assert "\\foo" not in out
    assert "סוף" in out


def test_unwraps_outer_markdown_fence():
    out = clean_narrative("```markdown\n## כותרת\n\nגוף.\n```\n")
    assert out.startswith("# כותרת")
    assert "```" not in out


def test_cuts_previously_appended_dashboard_for_idempotency():
    narrative = "## מבוא\n\nגוף.\n"
    appended = narrative + "\n## לוח נתונים — גודל השוק\n\n```{=latex}\nx\n```\n"
    out = clean_narrative(appended)
    assert "לוח נתונים" not in out
    assert "# מבוא" in out


def test_legacy_tail_marker_also_cut():
    out = clean_narrative("## מבוא\n\nגוף.\n\n## נתוני שוק\n\nישן.\n")
    assert "נתוני שוק" not in out
    assert "# מבוא" in out


def test_strips_raw_markdown_pipe_table():
    text = (
        "## גודל השוק\n\nפסקה לפני.\n\n"
        "| מדד | ערך |\n| :--- | ---: |\n| TAM | 100 |\n| SAM | 40 |\n\n"
        "פסקה אחרי.\n"
    )
    out = clean_narrative(text)
    assert "| TAM | 100 |" not in out
    assert ":---" not in out
    assert "פסקה לפני." in out
    assert "פסקה אחרי." in out


def test_thematic_break_is_not_treated_as_table():
    out = clean_narrative("## א\n\nטקסט.\n\n---\n\nעוד טקסט.\n")
    assert "עוד טקסט." in out
    assert "טקסט." in out


def test_promotes_nested_headings_to_top_level():
    text = "## תקציר\n\nא.\n\n## שוק\n\n### TAM\n\nב.\n"
    out = clean_narrative(text)
    assert out.startswith("# תקציר")  # ## -> #
    assert "## TAM" in out  # ### -> ##
    assert "###" not in out


def test_strips_literal_heading_numbers():
    # A leading title is dropped first; the numbered sections below survive.
    text = "# כותרת ראשית\n\n# 1. מבוא\n\nא.\n\n## 3.1. TAM\n\nב.\n"
    out = clean_narrative(text)
    assert "# מבוא" in out
    assert "## TAM" in out
    assert "3.1." not in out and "1. מבוא" not in out


def test_keeps_non_enumerator_heading_text():
    out = clean_narrative("## שלב 1: צמיחה\n\nגוף.\n")
    assert "שלב 1: צמיחה" in out


def test_heading_normalization_is_noop_when_already_top_level():
    out = clean_narrative("## א\n\nגוף.\n\n# ב\n\nעוד.\n")
    assert "## א" in out and "# ב" in out


def test_plain_prose_passes_through_unchanged():
    text = "## א\n\nפסקה ראשונה.\n\n## ב\n\nפסקה שנייה.\n"
    out = clean_narrative(text)
    assert "פסקה ראשונה." in out and "פסקה שנייה." in out
    assert out.endswith("\n")
