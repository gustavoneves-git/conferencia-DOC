from app.services.file_naming_service import clean_document_name, output_name, safe_filename


def test_safe_filename_keeps_suffix():
    assert safe_filename("Minha Minuta.pdf").endswith("_Minha_Minuta.pdf")


def test_output_name_has_suffix():
    assert output_name(3, "relatorio", "pdf").endswith(".pdf")


def test_output_name_uses_professional_document_name():
    name = output_name(3, "relatorio", "pdf", "GOGA - Contrato Social.pdf")
    assert name.startswith("GOGA - Contrato Social__relatorio_tecnico__")
    assert name.endswith(".pdf")
    assert "doc_3" not in name


def test_output_name_maps_corrected_and_final_labels():
    corrected = output_name(3, "corrigido", "docx", "Minuta.pdf")
    final = output_name(3, "final", "pdf", "Minuta.pdf")
    assert "__corrigido_revisao__" in corrected
    assert "__final_protocolo__" in final


def test_clean_document_name_removes_invalid_characters_and_limits_size():
    cleaned = clean_document_name('Contrato: Social / Teste * "ABC".pdf')
    assert ":" not in cleaned
    assert "/" not in cleaned
    assert "*" not in cleaned
    assert len(cleaned) <= 95
