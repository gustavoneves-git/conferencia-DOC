from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.file_naming_service import output_name


class ReportPdfService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def generate(self, document_id, document, session_id, issues, totals):
        target = self.base_dir / "storage" / "reports" / output_name(document_id, "relatorio", "pdf")
        c = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        y = self._header(c, width, height, "Relatório técnico de revisão")
        c.setFont("Helvetica", 9)
        summary_rows = [
            f"Documento: {document['original_filename']}",
            f"Tipo documental estimado: {document['document_type'] or '-'}",
            f"Empresa identificada: {document['company_name'] or '-'}",
            f"Total de apontamentos: {totals['total']}",
            f"Distribuição por gravidade: Baixa {totals['BAIXA']} | Média {totals['MEDIA']} | Alta {totals['ALTA']} | Crítica {totals['CRITICA']} | Conferir {totals['CONFERIR']}",
        ]
        for row in summary_rows:
            y = self._draw_wrapped(c, y, row, height, "Helvetica", 9)
        y -= 8
        c.setFont("Helvetica-Oblique", 8)
        y = self._draw_wrapped(c, y, "Este relatório exige revisão humana e não substitui avaliação jurídica profissional.", height, "Helvetica-Oblique", 8)
        y -= 18
        c.setFont("Helvetica", 9)
        for issue in issues:
            if y < 110:
                c.showPage()
                y = self._header(c, width, height, "Relatório técnico de revisão")
            c.setFillColor(colors.HexColor("#f1f4f8"))
            c.rect(40, y - 4, width - 80, 18, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#1f2933"))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(48, y, f"{issue['code']} | Página {issue.get('page_number') or '-'} | {issue['issue_type']} | {issue['severity']} | Fonte {issue.get('source', '-')}")
            y -= 18
            c.setFont("Helvetica", 9)
            rows = [
                f"Trecho original: {issue.get('original_text') or '-'}",
                f"Explicação: {issue.get('explanation') or '-'}",
                f"Sugestão: {issue.get('suggestion') or '-'}",
                f"Justificativa técnica: {issue.get('technical_reason') or '-'}",
                f"Ação recomendada: {issue.get('recommended_action') or '-'}",
            ]
            for row in rows:
                y = self._draw_wrapped(c, y, row, height, "Helvetica", 9)
            y -= 8
        c.save()
        return str(target)

    def _header(self, c, width, height, title):
        c.setFillColor(colors.HexColor("#145c4b"))
        c.rect(0, height - 42, width, 42, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(45, height - 27, f"Conferência Documento - {title}")
        c.setFillColor(colors.HexColor("#1f2933"))
        return height - 65

    def _draw_wrapped(self, c, y, text, height, font, size):
        c.setFont(font, size)
        for line in self._wrap(text, 112):
            if y < 58:
                c.showPage()
                y = self._header(c, A4[0], height, "Relatório técnico de revisão")
                c.setFont(font, size)
            c.drawString(45, y, line)
            y -= 13
        return y

    def _wrap(self, text, size):
        return [text[i:i + size] for i in range(0, len(text), size)] or [""]
