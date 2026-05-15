from app.services.text_extraction_service import TextExtractionService


def test_normalize_removes_blank_lines():
    text = TextExtractionService().normalize(" linha   um \n\n linha dois ")
    assert text == "linha um\nlinha dois"
