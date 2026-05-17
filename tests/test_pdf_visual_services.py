from pathlib import Path

import fitz
from reportlab.pdfgen import canvas

from app.services.pdf_annotation_service import PdfAnnotationService
from app.services.pdf_visual_style import SEVERITY_STYLES, ProfessionalPdfLayout, severity_style, wrap_text
from app.services.report_pdf_service import ReportPdfService


def test_severity_styles_are_mapped():
    assert set(SEVERITY_STYLES) == {"CRITICA", "ALTA", "MEDIA", "BAIXA", "CONFERIR"}
    assert severity_style("ALTA")["fill"]


def test_wrap_text_does_not_split_words_when_possible():
    lines = wrap_text("texto profissional com várias palavras para quebra limpa", 18)
    assert all(len(line) <= 18 for line in lines)
    assert "profissional" in " ".join(lines)


def test_report_pdf_generates_with_long_issue(tmp_path):
    service = ReportPdfService(tmp_path)
    (tmp_path / "storage" / "reports").mkdir(parents=True)
    document = {
        "original_filename": "Contrato Social de Teste.pdf",
        "document_type": "CONTRATO_SOCIAL_CONSTITUICAO_LTDA",
        "company_name": "EMPRESA TESTE LTDA",
    }
    issues = [
        {
            "code": "E001",
            "page_number": 1,
            "issue_type": "REDACAO_FRACA",
            "severity": "MEDIA",
            "source": "BOTH",
            "located_in_pdf": True,
            "location_strategy": "EXACT",
            "original_text": "trecho longo " * 40,
            "explanation": "explicação longa " * 20,
            "suggestion": "sugestão objetiva",
            "technical_reason": "justificativa técnica",
            "recommended_action": "ação recomendada",
        }
    ]
    totals = {"total": 1, "BAIXA": 0, "MEDIA": 1, "ALTA": 0, "CRITICA": 0, "CONFERIR": 0}
    path = service.generate(1, document, 1, issues, totals)
    assert Path(path).exists()
    assert "relatorio_tecnico" in Path(path).name


def test_pdf_grifado_still_generates(tmp_path):
    base = tmp_path
    for folder in ("storage/annotated", "storage/tmp"):
        (base / folder).mkdir(parents=True)
    original = base / "original.pdf"
    c = canvas.Canvas(str(original))
    c.drawString(72, 720, "O sócio administrador, poderá representar a sociedade.")
    c.save()
    issues = [
        {
            "code": "E001",
            "page_number": 1,
            "issue_type": "PONTUACAO",
            "severity": "MEDIA",
            "source": "RULE",
            "can_be_highlighted": True,
            "original_text": "O sócio administrador, poderá",
            "explanation": "Vírgula indevida.",
            "suggestion": "O sócio administrador poderá",
            "technical_reason": "Pontuação.",
            "recommended_action": "Corrigir.",
        }
    ]
    document = {"original_filename": "Teste.pdf", "document_type": "CONTRATO", "company_name": "TESTE LTDA"}
    totals = {"total": 1, "BAIXA": 0, "MEDIA": 1, "ALTA": 0, "CRITICA": 0, "CONFERIR": 0}
    path = PdfAnnotationService(base).generate(1, str(original), issues, document, totals)
    assert Path(path).exists()
    with fitz.open(path) as generated:
        assert len(generated) >= 2
