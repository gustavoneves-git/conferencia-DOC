import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class DocxOutputService:
    def create_docx(self, path: str, title: str, text: str, company: str | None = None) -> str:
        doc = Document()
        section = doc.sections[0]
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        styles = doc.styles["Normal"]
        styles.font.name = "Times New Roman"
        styles.font.size = Pt(12)
        if title:
            self._centered(doc, title.upper(), bold=True, size=13)
        if company:
            self._centered(doc, company.upper(), bold=True, size=12)
        if title or company:
            doc.add_paragraph()

        for line in self._clean_text(text).splitlines():
            if not line.strip():
                doc.add_paragraph()
                continue
            p = doc.add_paragraph()
            stripped = line.strip()
            run = p.add_run(stripped)
            if self._is_heading(stripped):
                run.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if self._is_major_heading(stripped) else WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(8)
            elif self._is_signature_line(stripped):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.keep_together = True
                p.paragraph_format.space_before = Pt(24)
                p.paragraph_format.space_after = Pt(10)
            elif self._is_location_date(stripped):
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p.paragraph_format.space_before = Pt(14)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.first_line_indent = Cm(1.25)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            p.paragraph_format.space_after = Pt(7)
            p.paragraph_format.line_spacing = 1.15
        doc.save(path)
        return path

    def create_pdf(self, path: str, title: str, text: str, company: str | None = None) -> str:
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=2.5 * cm,
            leftMargin=2.5 * cm,
            topMargin=2.5 * cm,
            bottomMargin=2.5 * cm,
        )
        styles = self._pdf_styles()
        story = []
        if title:
            story.append(Paragraph(self._escape(title.upper()), styles["Title"]))
        if company:
            story.append(Paragraph(self._escape(company.upper()), styles["Company"]))
        if title or company:
            story.append(Spacer(1, 18))
        for raw in self._clean_text(text).splitlines():
            stripped = raw.strip()
            if not stripped:
                story.append(Spacer(1, 8))
                continue
            if self._is_heading(stripped):
                style = styles["MajorHeading"] if self._is_major_heading(stripped) else styles["Heading"]
            elif self._is_signature_line(stripped):
                style = styles["Signature"]
            elif self._is_location_date(stripped):
                style = styles["Date"]
            else:
                style = styles["Body"]
            story.append(Paragraph(self._escape(stripped), style))
        doc.build(story)
        return path

    def _centered(self, doc, text, bold=False, size=11):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(text)
        run.bold = bold
        run.font.name = "Times New Roman"
        run.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(6)

    def _is_heading(self, text: str) -> bool:
        upper = text.upper()
        return upper.startswith((
            "CLÁUSULA", "CLAUSULA", "ARTIGO", "ART.", "CAPÍTULO", "CAPITULO",
            "PARÁGRAFO", "PARAGRAFO", "SEÇÃO", "SECAO",
        ))

    def _is_major_heading(self, text: str) -> bool:
        upper = text.upper()
        return upper.startswith(("CAPÍTULO", "CAPITULO", "SEÇÃO", "SECAO"))

    def _is_signature_line(self, text: str) -> bool:
        return "________________" in text or text.upper() in {"ASSINATURAS", "SÓCIOS", "SOCIOS", "TESTEMUNHAS"}

    def _is_location_date(self, text: str) -> bool:
        return bool(re.search(r",\s*\d{1,2}\s+de\s+\w+\s+de\s+\d{4}\.?$", text, re.IGNORECASE))

    def _clean_text(self, text: str | None) -> str:
        lines = []
        blank = 0
        for raw in (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            line = re.sub(r"[ \t]+", " ", raw).strip()
            if not line:
                blank += 1
                if blank <= 1:
                    lines.append("")
                continue
            blank = 0
            lines.append(line)
        return "\n".join(lines).strip()

    def _pdf_styles(self):
        base = getSampleStyleSheet()
        return {
            "Title": ParagraphStyle(
                "DocumentTitle", parent=base["Title"], fontName="Times-Bold",
                fontSize=13, leading=16, alignment=1, spaceAfter=8,
            ),
            "Company": ParagraphStyle(
                "Company", parent=base["Normal"], fontName="Times-Bold",
                fontSize=12, leading=15, alignment=1, spaceAfter=6,
            ),
            "MajorHeading": ParagraphStyle(
                "MajorHeading", parent=base["Heading2"], fontName="Times-Bold",
                fontSize=12, leading=15, alignment=1, spaceBefore=12, spaceAfter=8,
                keepWithNext=True,
            ),
            "Heading": ParagraphStyle(
                "Heading", parent=base["Normal"], fontName="Times-Bold",
                fontSize=12, leading=15, alignment=0, spaceBefore=10, spaceAfter=7,
                keepWithNext=True,
            ),
            "Body": ParagraphStyle(
                "Body", parent=base["Normal"], fontName="Times-Roman",
                fontSize=12, leading=15, alignment=4, firstLineIndent=1.25 * cm,
                spaceAfter=7, splitLongWords=False,
            ),
            "Signature": ParagraphStyle(
                "Signature", parent=base["Normal"], fontName="Times-Roman",
                fontSize=12, leading=16, alignment=1, spaceBefore=24, spaceAfter=10,
                keepTogether=True,
            ),
            "Date": ParagraphStyle(
                "Date", parent=base["Normal"], fontName="Times-Roman",
                fontSize=12, leading=15, alignment=2, spaceBefore=14, spaceAfter=8,
            ),
        }

    def _escape(self, text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
