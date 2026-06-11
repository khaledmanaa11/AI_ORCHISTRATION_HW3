from reasearch_crew import settings


def _template_text():
    return settings.template_path().read_text(encoding="utf-8")


def test_template_exists_at_configured_path():
    assert settings.template_path().exists()


def test_font_token_substituted_not_hardcoded():
    text = _template_text()
    # The font is a pandoc variable token, not the literal book.json value.
    assert "$hebrewfont$" in text
    assert settings.book_config()["hebrew_font"] not in text  # e.g. "David"


def test_loads_required_packages():
    text = _template_text()
    for pkg in ("polyglossia", "booktabs", "pgfplots", "graphicx", "fontspec"):
        assert pkg in text, f"template missing {pkg}"


def test_hebrew_is_main_language():
    text = _template_text()
    assert "\\setmainlanguage{hebrew}" in text


def test_has_pandoc_body_placeholder_and_no_report_prose():
    text = _template_text()
    assert "$body$" in text
    # No baked-in report content — the template is structure only.
    assert "אליאסמין" not in text
    assert "ALYASMEEN" not in text
