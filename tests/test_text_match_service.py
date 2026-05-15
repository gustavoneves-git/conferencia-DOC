from app.services.text_match_service import text_contains


def test_text_contains_ignores_accents_and_extra_spaces():
    page_text = "O sócio administrador poderá representar a sociedade."
    issue_text = "O socio   administrador podera"
    assert text_contains(page_text, issue_text)
