from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4


BRAND_GREEN = colors.HexColor("#145c4b")
TEXT = colors.HexColor("#1f2933")
MUTED = colors.HexColor("#6b7280")
LIGHT_BORDER = colors.HexColor("#d7dee8")
SOFT_BG = colors.HexColor("#f7f9fb")

SEVERITY_STYLES = {
    "CRITICA": {"fill": colors.HexColor("#f9d4d4"), "stroke": colors.HexColor("#b42318"), "text": colors.HexColor("#7a1c16")},
    "ALTA": {"fill": colors.HexColor("#fde2cf"), "stroke": colors.HexColor("#c2410c"), "text": colors.HexColor("#7c2d12")},
    "MEDIA": {"fill": colors.HexColor("#fff1bf"), "stroke": colors.HexColor("#b7791f"), "text": colors.HexColor("#704214")},
    "BAIXA": {"fill": colors.HexColor("#dcecff"), "stroke": colors.HexColor("#2b6cb0"), "text": colors.HexColor("#1e4e8c")},
    "CONFERIR": {"fill": colors.HexColor("#eadcf8"), "stroke": colors.HexColor("#6b46c1"), "text": colors.HexColor("#44337a")},
}


def severity_style(severity: str | None) -> dict:
    return SEVERITY_STYLES.get(str(severity or "").upper(), {"fill": colors.HexColor("#e5e7eb"), "stroke": MUTED, "text": TEXT})


def source_label(source):
    return {"BOTH": "Regra + IA", "RULE": "Regra", "AI": "IA"}.get(source or "", source or "-")


def wrap_text(text, max_chars):
    words = str(text or "").split()
    if not words:
        return [""]
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:max_chars]
    if current:
        lines.append(current)
    return lines


class ProfessionalPdfLayout:
    def __init__(self, canvas, title: str):
        self.c = canvas
        self.title = title
        self.width, self.height = A4
        self.margin_x = 42
        self.bottom = 44
        self.page_number = 0

    def new_page(self):
        if self.page_number:
            self.footer()
            self.c.showPage()
        self.page_number += 1
        self.header()
        return self.height - 72

    def header(self):
        self.c.setFillColor(BRAND_GREEN)
        self.c.rect(0, self.height - 38, self.width, 38, fill=1, stroke=0)
        self.c.setFillColor(colors.white)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(self.margin_x, self.height - 24, "Conferência Documento")
        self.c.setFont("Helvetica", 8)
        self.c.drawRightString(self.width - self.margin_x, self.height - 24, self.title)
        self.c.setFillColor(TEXT)

    def footer(self):
        self.c.setStrokeColor(LIGHT_BORDER)
        self.c.line(self.margin_x, 32, self.width - self.margin_x, 32)
        self.c.setFillColor(MUTED)
        self.c.setFont("Helvetica", 7)
        self.c.drawString(self.margin_x, 20, "Ferramenta de apoio operacional. Revisão humana é obrigatória.")
        self.c.drawRightString(self.width - self.margin_x, 20, f"Página {self.page_number}")
        self.c.setFillColor(TEXT)

    def finish(self):
        self.footer()

    def ensure_space(self, y, needed):
        if y - needed < self.bottom:
            return self.new_page()
        return y

    def text(self, x, y, value, font="Helvetica", size=9, fill=TEXT):
        self.c.setFillColor(fill)
        self.c.setFont(font, size)
        self.c.drawString(x, y, str(value or ""))
        self.c.setFillColor(TEXT)

    def draw_wrapped(self, x, y, text, max_chars=96, font="Helvetica", size=8.5, leading=11, fill=TEXT):
        self.c.setFont(font, size)
        self.c.setFillColor(fill)
        for line in wrap_text(text, max_chars):
            y = self.ensure_space(y, leading + 4)
            self.c.drawString(x, y, line)
            y -= leading
        self.c.setFillColor(TEXT)
        return y

    def section_title(self, y, title):
        y = self.ensure_space(y, 26)
        self.c.setFillColor(TEXT)
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(self.margin_x, y, title)
        y -= 7
        self.c.setStrokeColor(LIGHT_BORDER)
        self.c.line(self.margin_x, y, self.width - self.margin_x, y)
        return y - 14

    def severity_tag(self, x, y, severity, width=58):
        style = severity_style(severity)
        self.c.setFillColor(style["fill"])
        self.c.setStrokeColor(style["stroke"])
        self.c.roundRect(x, y - 3, width, 13, 2, fill=1, stroke=1)
        self.c.setFillColor(style["text"])
        self.c.setFont("Helvetica-Bold", 6.8)
        self.c.drawCentredString(x + width / 2, y + 1, str(severity or "-")[:10])
        self.c.setFillColor(TEXT)

    def legend(self, y):
        y = self.ensure_space(y, 48)
        self.c.setFont("Helvetica", 8)
        self.c.setFillColor(MUTED)
        self.c.drawString(self.margin_x, y, "Legenda de prioridade operacional:")
        x = self.margin_x + 150
        for severity in ["CRITICA", "ALTA", "MEDIA", "BAIXA", "CONFERIR"]:
            self.severity_tag(x, y, severity, width=54)
            x += 62
        return y - 18

    def generated_at(self):
        return datetime.now().strftime("%d/%m/%Y %H:%M")
