from pathlib import Path

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
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(45, y, "Conferencia Documento - Relatorio Tecnico")
        y -= 24
        c.setFont("Helvetica", 9)
        c.drawString(45, y, f"Documento: {document['original_filename']}")
        y -= 14
        c.drawString(45, y, f"Empresa: {document['company_name'] or '-'}")
        y -= 14
        c.drawString(45, y, f"Total: {totals['total']} | Baixa: {totals['BAIXA']} | Media: {totals['MEDIA']} | Alta: {totals['ALTA']} | Critica: {totals['CRITICA']} | Conferir: {totals['CONFERIR']}")
        y -= 24
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(45, y, "Este relatorio exige revisao humana e nao substitui avaliacao juridica profissional.")
        y -= 28
        c.setFont("Helvetica", 9)
        for issue in issues:
            rows = [
                f"{issue['code']} | Pagina {issue.get('page_number') or '-'} | {issue['issue_type']} | {issue['severity']}",
                f"Trecho: {issue.get('original_text') or '-'}",
                f"Explicacao: {issue.get('explanation') or '-'}",
                f"Justificativa: {issue.get('technical_reason') or '-'}",
                f"Sugestao: {issue.get('suggestion') or '-'}",
                f"Acao recomendada: {issue.get('recommended_action') or '-'}",
            ]
            for row in rows:
                for line in self._wrap(row, 112):
                    if y < 60:
                        c.showPage()
                        c.setFont("Helvetica", 9)
                        y = height - 50
                    c.drawString(45, y, line)
                    y -= 13
            y -= 8
        c.save()
        return str(target)

    def _wrap(self, text, size):
        return [text[i:i + size] for i in range(0, len(text), size)] or [""]
