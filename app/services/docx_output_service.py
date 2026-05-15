from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class DocxOutputService:
    def create_docx(self, path: str, title: str, text: str) -> str:
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        styles = doc.styles["Normal"]
        styles.font.name = "Arial"
        styles.font.size = Pt(11)
        if title:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(title.upper())
            run.bold = True
        for line in (text or "").splitlines():
            p = doc.add_paragraph()
            stripped = line.strip()
            run = p.add_run(stripped)
            if stripped.upper().startswith(("CLÁUSULA", "CLAUSULA", "ARTIGO", "CAPÍTULO", "CAPITULO")):
                run.bold = True
            p.paragraph_format.space_after = Pt(6)
        doc.save(path)
        return path

    def create_pdf(self, path: str, title: str, text: str) -> str:
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        y = height - 55
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, y, (title or "Documento").upper()[:90])
        y -= 30
        c.setFont("Helvetica", 10)
        for raw in (text or "").splitlines():
            for line in self._wrap(raw.strip(), 105):
                if y < 55:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 55
                c.drawString(55, y, line)
                y -= 14
        c.save()
        return path

    def _wrap(self, text, size):
        return [text[i:i + size] for i in range(0, len(text), size)] or [""]
