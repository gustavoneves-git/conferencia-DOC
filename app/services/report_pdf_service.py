from collections import Counter
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.file_naming_service import output_name
from app.services.pdf_visual_style import (
    LIGHT_BORDER,
    MUTED,
    SOFT_BG,
    TEXT,
    ProfessionalPdfLayout,
    source_label,
    wrap_text,
)


class ReportPdfService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def generate(self, document_id, document, session_id, issues, totals, session=None):
        target = self.base_dir / "storage" / "reports" / output_name(
            document_id, "relatorio", "pdf", document["original_filename"]
        )
        c = canvas.Canvas(str(target), pagesize=A4)
        layout = ProfessionalPdfLayout(c, "Relatório técnico de revisão")
        y = layout.new_page()
        y = self._cover(layout, y, document, issues, totals, session)
        y = self._summary_table(layout, y, issues)
        y = self._issue_details(layout, y, issues)
        layout.finish()
        c.save()
        return str(target)

    def _cover(self, layout, y, document, issues, totals, session):
        c = layout.c
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Bold", 18)
        c.drawString(layout.margin_x, y, "Relatório Técnico de Revisão")
        y -= 18
        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        c.drawString(layout.margin_x, y, "Conferência Documento")
        y -= 26

        by_source = Counter(issue.get("source") for issue in issues)
        located = sum(1 for issue in issues if issue.get("located_in_pdf"))
        not_located = len(issues) - located
        rows = [
            ("Documento analisado", document["original_filename"]),
            ("Empresa identificada", document["company_name"] or "-"),
            ("Tipo documental estimado", document["document_type"] or "-"),
            ("Modo de análise", getattr(session, "ai_mode", None) or (session["ai_mode"] if session else "-")),
            ("Modelo usado", getattr(session, "model_used", None) or (session["model_used"] if session else "-")),
            ("Data/hora da análise", layout.generated_at()),
            ("Total de apontamentos", totals["total"]),
            ("Total por origem", f"Regra {by_source.get('RULE', 0)} | IA {by_source.get('AI', 0)} | Regra + IA {by_source.get('BOTH', 0)}"),
            ("Localização no PDF", f"Localizados {located} | Não localizados {not_located}"),
            ("Risk score", self._risk_score(totals)),
            ("Risk level", self._risk_level(totals)),
        ]
        y = self._info_grid(layout, y, rows)
        y = layout.section_title(y - 4, "Distribuição por gravidade")
        y = layout.legend(y)
        gravity = f"Baixa {totals['BAIXA']} | Média {totals['MEDIA']} | Alta {totals['ALTA']} | Crítica {totals['CRITICA']} | Conferir {totals['CONFERIR']}"
        y = layout.draw_wrapped(layout.margin_x, y, gravity, 110, "Helvetica-Bold", 9)
        y -= 12
        c.setFillColor(colors.HexColor("#fff8e8"))
        c.setStrokeColor(colors.HexColor("#ead9b7"))
        c.roundRect(layout.margin_x, y - 38, layout.width - 2 * layout.margin_x, 34, 4, fill=1, stroke=1)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(layout.margin_x + 10, y - 17, "Este relatório é uma ferramenta de apoio operacional e não substitui revisão jurídica profissional.")
        return y - 58

    def _info_grid(self, layout, y, rows):
        left = layout.margin_x
        label_w = 128
        value_w = layout.width - 2 * layout.margin_x - label_w
        for label, value in rows:
            y = layout.ensure_space(y, 23)
            layout.c.setFillColor(SOFT_BG)
            layout.c.setStrokeColor(LIGHT_BORDER)
            layout.c.rect(left, y - 5, label_w + value_w, 18, fill=1, stroke=1)
            layout.text(left + 7, y, label, "Helvetica-Bold", 8, MUTED)
            layout.text(left + label_w + 7, y, str(value or "-")[:105], "Helvetica", 8, TEXT)
            y -= 18
        return y

    def _summary_table(self, layout, y, issues):
        y = layout.section_title(y, "Sumário de Apontamentos")
        headers = [("Código", 44), ("Pág.", 32), ("Gravidade", 64), ("Tipo", 104), ("Fonte", 66), ("Trecho resumido", 200)]
        y = self._table_header(layout, y, headers)
        for issue in issues:
            y = layout.ensure_space(y, 24)
            x = layout.margin_x
            row_values = [
                issue.get("code"),
                issue.get("page_number") or "-",
                issue.get("severity"),
                issue.get("issue_type"),
                source_label(issue.get("source")),
                self._short(issue.get("original_text"), 74),
            ]
            layout.c.setFont("Helvetica", 7.2)
            for value, (_, width) in zip(row_values, headers):
                if _ == "Gravidade":
                    layout.severity_tag(x, y + 1, value, width=56)
                else:
                    layout.c.setFillColor(TEXT)
                    layout.c.drawString(x + 3, y + 1, str(value or "-")[: max(8, int(width / 4.2))])
                x += width
            layout.c.setStrokeColor(LIGHT_BORDER)
            layout.c.line(layout.margin_x, y - 4, layout.width - layout.margin_x, y - 4)
            y -= 16
        return y - 12

    def _table_header(self, layout, y, headers):
        y = layout.ensure_space(y, 24)
        layout.c.setFillColor(TEXT)
        layout.c.setFont("Helvetica-Bold", 7.4)
        x = layout.margin_x
        for label, width in headers:
            layout.c.drawString(x + 3, y, label)
            x += width
        layout.c.setStrokeColor(LIGHT_BORDER)
        layout.c.line(layout.margin_x, y - 5, layout.width - layout.margin_x, y - 5)
        return y - 17

    def _issue_details(self, layout, y, issues):
        y = layout.section_title(y, "Detalhamento dos Apontamentos")
        for issue in issues:
            y = self._issue_card(layout, y, issue)
        return y

    def _issue_card(self, layout, y, issue):
        estimated = self._estimate_card_height(issue)
        y = layout.ensure_space(y, min(estimated, layout.height - 120))
        top = y
        layout.c.setFillColor(colors.white)
        layout.c.setStrokeColor(LIGHT_BORDER)
        layout.c.roundRect(layout.margin_x, y - estimated + 8, layout.width - 2 * layout.margin_x, estimated, 5, fill=1, stroke=1)
        x = layout.margin_x + 10
        layout.text(x, y - 8, issue.get("code"), "Helvetica-Bold", 10)
        layout.severity_tag(x + 46, y - 8, issue.get("severity"), width=62)
        meta = f"Página {issue.get('page_number') or '-'} | {issue.get('issue_type')} | Fonte: {source_label(issue.get('source'))}"
        layout.text(x + 118, y - 8, meta, "Helvetica", 8, MUTED)
        y -= 28
        if issue.get("location_strategy"):
            y = layout.draw_wrapped(x, y, f"Estratégia de localização: {issue.get('location_strategy')}", 102, "Helvetica", 7.7, 10, MUTED)
        if issue.get("repeated_group_id"):
            y = layout.draw_wrapped(x, y, f"Ocorrência repetida: sim | Grupo: {issue.get('repeated_group_id')} ({issue.get('repeated_count') or 0} ocorrências)", 102, "Helvetica", 7.7, 10, MUTED)
        fields = [
            ("Trecho original", issue.get("original_text")),
            ("Explicação", issue.get("explanation")),
            ("Sugestão", issue.get("suggestion")),
            ("Justificativa técnica", issue.get("technical_reason")),
            ("Ação recomendada", issue.get("recommended_action")),
        ]
        for label, value in fields:
            y = layout.draw_wrapped(x, y, f"{label}: {value or '-'}", 98, "Helvetica", 8.2, 10.5)
            y -= 2
        return min(y - 12, top - estimated - 4)

    def _estimate_card_height(self, issue):
        count = 3
        for key in ("original_text", "explanation", "suggestion", "technical_reason", "recommended_action"):
            count += len(wrap_text(issue.get(key), 98))
        if issue.get("location_strategy"):
            count += 1
        if issue.get("repeated_group_id"):
            count += 1
        return max(78, 30 + count * 11)

    def _short(self, text, limit):
        text = " ".join(str(text or "").split())
        return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."

    def _risk_score(self, totals):
        return totals["CRITICA"] * 100 + totals["ALTA"] * 20 + totals["MEDIA"] * 8 + totals["CONFERIR"] * 5 + totals["BAIXA"] * 2

    def _risk_level(self, totals):
        if totals["total"] == 0:
            return "SEM_APONTAMENTOS"
        if totals["CRITICA"] or totals["ALTA"] > 5:
            return "CRITICO"
        if totals["ALTA"] or totals["MEDIA"] >= 8:
            return "ALTO"
        if totals["MEDIA"] or totals["CONFERIR"]:
            return "MEDIO"
        return "BAIXO"
