from reasearch_crew.report.outline import section_outline


def test_outline_meets_page_target():
    cfg_pages = 3
    outline = section_outline(page_target=30, pages_per_section=cfg_pages)
    assert len(outline) * cfg_pages >= 30
    assert all(isinstance(s, str) and s for s in outline)


def test_outline_pads_when_target_is_large():
    outline = section_outline(page_target=90, pages_per_section=3)
    assert len(outline) >= 30  # 90/3, padded beyond the base list


def test_outline_defaults_from_book_json():
    outline = section_outline()
    assert len(outline) >= 1
    assert "תקציר מנהלים" in outline


# ── compose_book unit tests (D16) ────────────────────────────────────────────

_FAKE_CFG = {
    "page_target": 9,
    "pages_per_section": 3,
    "words_per_page": 400,
    "paths": {"book_md": "output/book.he.md"},
}


class _FakeLLM:
    def __init__(self):
        self.calls: list[list[dict]] = []

    def call(self, messages, *args, **kwargs):
        self.calls.append(messages)
        return {"choices": [{"message": {"content": "stub text"}}], "usage": {}}


def test_compose_calls_once_per_section(tmp_path, monkeypatch):
    from reasearch_crew import settings as _s
    monkeypatch.setattr(_s, "book_config", lambda *a, **k: _FAKE_CFG)
    from reasearch_crew.report.compose import compose_book

    llm = _FakeLLM()
    compose_book(llm, "brief", tmp_path / "book.he.md")

    expected = section_outline(page_target=9, pages_per_section=3)
    assert len(llm.calls) == len(expected)


def test_compose_headings_in_order(tmp_path, monkeypatch):
    from reasearch_crew import settings as _s
    monkeypatch.setattr(_s, "book_config", lambda *a, **k: _FAKE_CFG)
    from reasearch_crew.report.compose import compose_book

    book_md = tmp_path / "book.he.md"
    compose_book(_FakeLLM(), "brief", book_md)

    content = book_md.read_text(encoding="utf-8")
    for sec in section_outline(page_target=9, pages_per_section=3):
        assert f"## {sec}" in content


def test_compose_word_floor_from_config(tmp_path, monkeypatch):
    from reasearch_crew import settings as _s
    monkeypatch.setattr(_s, "book_config", lambda *a, **k: _FAKE_CFG)
    from reasearch_crew.report.compose import compose_book

    llm = _FakeLLM()
    compose_book(llm, "brief", tmp_path / "book.he.md")

    # min_words must come from config (400 * 3 = 1200), not a literal
    expected_floor = str(_FAKE_CFG["words_per_page"] * _FAKE_CFG["pages_per_section"])
    assert expected_floor in llm.calls[0][0]["content"]
