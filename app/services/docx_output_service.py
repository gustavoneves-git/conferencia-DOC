from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


class DocxOutputService:
    def create_docx(self, path: str, title: str, text: str, company: str | None = None) -> str:
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
            self._centered(doc, title.upper(), bold=True, size=12)
        if company:
            self._centered(doc, company.upper(), bold=True, size=11)
        if title or company:
            doc.add_paragraph()

        for line in (text or "").splitlines():
            if not line.strip():
                doc.add_paragraph()
                continue
            p = doc.add_paragraph()
            stripped = line.strip()
            run = p.add_run(stripped)
            if self._is_heading(stripped):
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif self._is_signature_line(stripped):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(20)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
        doc.save(path)
        return path

    def create_pdf(self, path: str, title: str, text: str, company: str | None = None) -> str:
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        y = height - 55
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(width / 2, y, (title or "Documento").upper()[:90])
        y -= 30
        if company:
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(width / 2, y, company.upper()[:100])
            y -= 28
        c.setFont("Helvetica", 10)
        for raw in (text or "").splitlines():
            if not raw.strip():
                y -= 10
                continue
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

    def _centered(self, doc, text, bold=False, size=11):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.name = "Arial"
        run.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(6)

    def _is_heading(self, text: str) -> bool:
        upper = text.upper()
        return upper.startswith(("CLÁUSULA", "CLAUSULA", "ARTIGO", "CAPÍTULO", "CAPITULO", "PARÁGRAFO", "PARAGRAFO"))

    def _is_signature_line(self, text: str) -> bool:
        return "________________" in text or text.upper() in {"ASSINATURAS", "SÓCIOS", "SOCIOS", "TESTEMUNHAS"}
