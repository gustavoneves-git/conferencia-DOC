import inspect

from app.services import pdf_annotation_service, report_pdf_service


def test_report_sources_use_accented_portuguese_labels():
    combined = inspect.getsource(report_pdf_service) + inspect.getsource(pdf_annotation_service)
    assert "Conferência Documento" in combined
    assert "Relatório técnico de revisão" in combined
    assert "Distribuição por gravidade" in combined
    assert "Explicação" in combined
    assert "Sugestão" in combined
    assert "Ação" in combined
