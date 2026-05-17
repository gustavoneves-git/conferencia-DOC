from pathlib import Path

import fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.file_naming_service import output_name
from app.services.pdf_visual_style import LIGHT_BORDER, MUTED, TEXT, ProfessionalPdfLayout, source_label, severity_style
from app.services.text_match_service import candidate_phrases, normalize_for_match


class PdfAnnotationService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def generate(self, document_id: int, original_path: str, issues: list[dict], document=None, totals=None) -> str | None:
        if Path(original_path).suffix.lower() != ".pdf":
            return None
        original_name = document["original_filename"] if document else None
        target = self.base_dir / "storage" / "annotated" / output_name(document_id, "grifado", "pdf", original_name)
        with fitz.open(original_path) as doc:
            label_offsets: dict[int, int] = {}
            for issue in issues:
                if not issue.get("can_be_highlighted") or not issue.get("original_text"):
                    continue
                pages = self._candidate_pages(issue.get("page_number"), len(doc))
                found = False
                for page_no in pages:
                    if not page_no or page_no < 1 or page_no > len(doc):
                        continue
                    page = doc[page_no - 1]
                    rects = self._find_rects(page, issue["original_text"])
                    if not rects:
                        continue
                    highlight_color = self._highlight_color(issue.get("severity"))
                    for rect in rects[:2]:
                        annot = page.add_highlight_annot(rect)
                        annot.set_colors(stroke=highlight_color)
                        annot.update(opacity=0.28)
                        annot.set_info(content=f"{issue['code']} - {issue['explanation']}")
                    label_rect = rects[0]
                    point = self._label_point(page, page_no, label_rect, label_offsets)
                    page.insert_text(point, issue["code"], fontsize=7.2, color=self._label_color(issue.get("severity")))
                    issue["located_in_pdf"] = True
                    issue["page_number"] = page_no
                    found = True
                    break
                if not found:
                    issue["located_in_pdf"] = False
                    issue["location_strategy"] = "NOT_FOUND"
            doc.save(target)
        report_pages = self._issue_appendix(document_id, issues, document, totals)
        self._append_pdf(target, report_pages)
        return str(target)

    def _find_rects(self, page, text: str):
        for candidate in candidate_phrases(text):
            rects = page.search_for(candidate)
            if rects:
                return rects
        return self._find_rects_by_words(page, text)

    def _candidate_pages(self, preferred_page, total_pages):
        try:
            preferred_page = int(preferred_page) if preferred_page else None
        except (TypeError, ValueError):
            preferred_page = None
        pages = []
        if preferred_page and 1 <= preferred_page <= total_pages:
            pages.append(preferred_page)
        pages.extend(page for page in range(1, total_pages + 1) if page not in pages)
        return pages

    def _find_rects_by_words(self, page, text: str):
        target_words = normalize_for_match(text).split()
        if not target_words:
            return []
        page_words = page.get_text("words")
        word_pairs = [(word, normalize_for_match(word[4])) for word in page_words]
        word_pairs = [(word, normalized) for word, normalized in word_pairs if normalized]
        normalized_words = [normalized for _, normalized in word_pairs]
        windows = self._target_windows(target_words)
        for window in windows:
            size = len(window)
            if size == 0:
                continue
            for idx in range(0, len(normalized_words) - size + 1):
                if normalized_words[idx : idx + size] == window:
                    rects = [fitz.Rect(*word_pairs[pos][0][:4]) for pos in range(idx, idx + size)]
                    return self._merge_line_rects(rects)
        return []

    def _target_windows(self, words):
        windows = [words]
        if len(words) > 14:
            windows.extend([words[:14], words[-14:]])
        if len(words) > 10:
            mid = len(words) // 2
            windows.append(words[max(0, mid - 5) : mid + 7])
        return windows

    def _merge_line_rects(self, rects):
        lines = []
        for rect in rects:
            placed = False
            for idx, line in enumerate(lines):
                if abs(line.y0 - rect.y0) < 4 or line.intersects(rect):
                    lines[idx] = line | rect
                    placed = True
                    break
            if not placed:
                lines.append(rect)
        return lines[:3]

    def _issue_appendix(self, document_id, issues, document=None, totals=None):
        original_name = document["original_filename"] if document else None
        path = self.base_dir / "storage" / "tmp" / output_name(document_id, "anexo_apontamentos", "pdf", original_name)
        c = canvas.Canvas(str(path), pagesize=A4)
        layout = ProfessionalPdfLayout(c, "Anexo do PDF grifado")
        y = layout.new_page()
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(TEXT)
        c.drawString(layout.margin_x, y, "Anexo do PDF Grifado")
        y -= 24
        if document:
            y = self._draw_info(layout, y, "Documento", document["original_filename"])
            y = self._draw_info(layout, y, "Tipo estimado", document["document_type"] or "-")
            y = self._draw_info(layout, y, "Empresa identificada", document["company_name"] or "-")
        if totals:
            y = self._draw_info(layout, y, "Total de apontamentos", totals["total"])
            y = layout.legend(y - 2)
            gravity = f"Baixa {totals['BAIXA']} | Média {totals['MEDIA']} | Alta {totals['ALTA']} | Crítica {totals['CRITICA']} | Conferir {totals['CONFERIR']}"
            y = layout.draw_wrapped(layout.margin_x, y, gravity, 110, "Helvetica-Bold", 8.5)
        y -= 8
        c.setFillColor(colors.HexColor("#fff8e8"))
        c.setStrokeColor(colors.HexColor("#ead9b7"))
        c.roundRect(layout.margin_x, y - 30, layout.width - 2 * layout.margin_x, 26, 4, fill=1, stroke=1)
        c.setFillColor(TEXT)
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(layout.margin_x + 8, y - 16, "A versão final exige revisão humana. Este sistema não substitui avaliação jurídica profissional.")
        y -= 46
        y = layout.section_title(y, "Apontamentos")
        for issue in issues:
            y = self._draw_issue_block(layout, y, issue)
        layout.finish()
        c.save()
        return path

    def _append_pdf(self, base, appendix):
        with fitz.open(base) as doc, fitz.open(appendix) as extra:
            doc.insert_pdf(extra)
            doc.saveIncr()

    def _draw_info(self, layout, y, label, value):
        y = layout.ensure_space(y, 18)
        layout.text(layout.margin_x, y, f"{label}:", "Helvetica-Bold", 8, MUTED)
        layout.text(layout.margin_x + 116, y, str(value or "-")[:105], "Helvetica", 8, TEXT)
        return y - 15

    def _draw_issue_block(self, layout, y, issue):
        y = layout.ensure_space(y, 76)
        x = layout.margin_x
        layout.c.setFillColor(colors.white)
        layout.c.setStrokeColor(LIGHT_BORDER)
        layout.c.roundRect(x, y - 72, layout.width - 2 * x, 72, 4, fill=1, stroke=1)
        layout.text(x + 8, y - 14, issue.get("code"), "Helvetica-Bold", 9)
        layout.severity_tag(x + 45, y - 14, issue.get("severity"), width=58)
        layout.text(
            x + 112,
            y - 14,
            f"Página {issue.get('page_number') or '-'} | {issue.get('issue_type')} | Fonte: {source_label(issue.get('source'))}",
            "Helvetica",
            7.7,
            MUTED,
        )
        yy = y - 29
        yy = layout.draw_wrapped(x + 8, yy, f"Trecho: {issue.get('original_text') or '-'}", 102, "Helvetica", 7.8, 9.5)
        yy = layout.draw_wrapped(x + 8, yy, f"Sugestão: {issue.get('suggestion') or '-'}", 102, "Helvetica", 7.8, 9.5)
        if issue.get("repeated_group_id"):
            yy = layout.draw_wrapped(x + 8, yy, f"Ocorrência repetida: sim | Grupo: {issue.get('repeated_group_id')}", 102, "Helvetica", 7.5, 9, MUTED)
        return min(yy - 10, y - 82)

    def _source_label(self, source):
        return {"BOTH": "Regra + IA", "RULE": "Regra", "AI": "IA"}.get(source or "", source or "-")

    def _highlight_color(self, severity):
        style = severity_style(severity)
        color = style["stroke"]
        return (color.red, color.green, color.blue)

    def _label_color(self, severity):
        style = severity_style(severity)
        color = style["text"]
        return (color.red, color.green, color.blue)

    def _label_point(self, page, page_no, label_rect, offsets):
        margin_x = 18 if label_rect.x0 > 56 else page.rect.width - 38
        base_y = min(max(label_rect.y0 + 8, 18), page.rect.height - 24)
        last_y = offsets.get(page_no, -999)
        if abs(base_y - last_y) < 11:
            base_y = min(last_y + 11, page.rect.height - 24)
        offsets[page_no] = base_y
        return fitz.Point(margin_x, base_y)
