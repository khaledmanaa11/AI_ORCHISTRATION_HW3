from reasearch_crew import settings


def test_book_config_is_hebrew():
    cfg = settings.book_config(force=True)
    assert cfg["language"] == "he"
    assert cfg["version"] == "1.00"
    assert cfg["hebrew_font"] == "David"
    assert cfg["page_target"] >= 30


def test_all_path_keys_present():
    paths = settings.book_config()["paths"]
    for key in (
        "research_md",
        "data_json",
        "book_md",
        "book_tex",
        "book_pdf",
        "template",
        "assets",
    ):
        assert key in paths, f"missing paths.{key}"


def test_bin_keys_present():
    binv = settings.book_config()["bin"]
    assert "pandoc" in binv
    assert "xelatex" in binv


def test_curated_asset_is_committed():
    assets = settings.asset_dir()
    assert assets.is_dir()
    images = list(assets.glob("*.png"))
    assert images, "no curated raster asset committed under assets/"
    assert images[0].stat().st_size > 0


def test_path_helpers_resolve_against_package():
    pkg = settings.package_dir()
    assert settings.template_path() == pkg / "templates" / "book.he.tex"
    assert settings.asset_dir() == pkg / "assets"
    assert str(settings.output_path("book_pdf")) == str(
        __import__("pathlib").Path("output/book.pdf")
    )
    settings.reset_cache()
