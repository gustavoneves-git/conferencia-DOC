from app.services.file_naming_service import output_name, safe_filename


def test_safe_filename_keeps_suffix():
    assert safe_filename("Minha Minuta.pdf").endswith("_Minha_Minuta.pdf")


def test_output_name_has_suffix():
    assert output_name(3, "relatorio", "pdf").endswith(".pdf")
