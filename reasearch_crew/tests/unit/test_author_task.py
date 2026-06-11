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


def test_author_task_targets_hebrew_book(api_key):
    from reasearch_crew.crew import ReasearchCrew

    crew_obj = ReasearchCrew().crew()
    author_task = next(
        t for t in crew_obj.tasks if t.output_file == "output/book.he.md"
    )
    out = author_task.expected_output
    for element in ("abstract", "table", "graph", "figure", "equations"):
        assert element in out
    author = next(a for a in crew_obj.agents if "מחבר" in a.role)
    assert author is not None
