from app.services.pdf_locator_service import PdfLocatorService


def test_locator_finds_long_text_by_key_phrase_and_records_strategy():
    issues = [
        {
            "page_number": 1,
            "original_text": (
                "A sócia administradora declara sob as penas da lei, não estar envolvida "
                "em crime falimentar, de prevaricação, peita ou suborno."
            ),
        }
    ]
    pages = [{"page_number": 1, "text": "A sócia administradora declara sob as penas da lei."}]
    marked = PdfLocatorService().mark_locations(issues, pages)
    assert marked[0]["located_in_pdf"] is True
    assert marked[0]["location_strategy"] in {"SUBSTRING", "KEY_PHRASE"}


def test_locator_normalizes_quotes_hyphens_and_spacing():
    issues = [{"page_number": 1, "original_text": "pró-labore"}]
    pages = [{"page_number": 1, "text": "retirada mensal, a título de “pró–labore”"}]
    marked = PdfLocatorService().mark_locations(issues, pages)
    assert marked[0]["located_in_pdf"] is True
    assert marked[0]["location_strategy"] in {"EXACT", "NORMALIZED", "KEY_PHRASE"}
