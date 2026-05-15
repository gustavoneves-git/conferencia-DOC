from pathlib import Path

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.file_naming_service import output_name


class PdfAnnotationService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def generate(self, document_id: int, original_path: str, issues: list[dict]) -> str | None:
        if Path(original_path).suffix.lower() != ".pdf":
            return None
        target = self.base_dir / "storage" / "annotated" / output_name(document_id, "grifado", "pdf")
        with fitz.open(original_path) as doc:
            for issue in issues:
                if not issue.get("can_be_highlighted") or not issue.get("original_text"):
                    continue
                pages = [issue.get("page_number")] if issue.get("page_number") else range(1, len(doc) + 1)
                found = False
                for page_no in pages:
                    if not page_no or page_no < 1 or page_no > len(doc):
                        continue
                    page = doc[page_no - 1]
                    rects = page.search_for(issue["original_text"])
                    if not rects:
                        continue
                    for rect in rects[:3]:
                        annot = page.add_highlight_annot(rect)
                        annot.set_info(content=f"{issue['code']} - {issue['explanation']}")
                        point = fitz.Point(rect.x1 + 4, rect.y0)
                        page.insert_text(point, issue["code"], fontsize=8, color=(0.7, 0, 0))
                    issue["located_in_pdf"] = True
                    found = True
                    break
                if not found:
                    issue["located_in_pdf"] = False
            doc.save(target)
        report_pages = self._issue_appendix(document_id, issues)
        self._append_pdf(target, report_pages)
        return str(target)

    def _issue_appendix(self, document_id, issues):
        path = self.base_dir / "storage" / "tmp" / output_name(document_id, "anexo_apontamentos", "pdf")
        c = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 13)
        c.drawString(50, y, "Anexo de apontamentos")
        y -= 30
        c.setFont("Helvetica", 9)
        for issue in issues:
            lines = [
                f"{issue['code']} | Pagina: {issue.get('page_number') or '-'} | {issue['issue_type']} | {issue['severity']}",
                f"Trecho: {issue.get('original_text') or '-'}",
                f"Explicacao: {issue.get('explanation') or '-'}",
                f"Sugestao: {issue.get('suggestion') or '-'}",
                f"Acao: {issue.get('recommended_action') or '-'}",
            ]
            for line in lines:
                for chunk in self._wrap(line, 110):
                    if y < 55:
                        c.showPage()
                        c.setFont("Helvetica", 9)
                        y = height - 50
                    c.drawString(50, y, chunk)
                    y -= 13
            y -= 8
        c.save()
        return path

    def _append_pdf(self, base, appendix):
        with fitz.open(base) as doc, fitz.open(appendix) as extra:
            doc.insert_pdf(extra)
            doc.saveIncr()

    def _wrap(self, text, size):
        return [text[i:i + size] for i in range(0, len(text), size)] or [""]
