from pathlib import Path

import fitz
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.services.file_naming_service import output_name
from app.services.text_match_service import candidate_phrases, normalize_for_match


class PdfAnnotationService:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def generate(self, document_id: int, original_path: str, issues: list[dict], document=None, totals=None) -> str | None:
        if Path(original_path).suffix.lower() != ".pdf":
            return None
        target = self.base_dir / "storage" / "annotated" / output_name(document_id, "grifado", "pdf")
        with fitz.open(original_path) as doc:
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
                    for rect in rects[:2]:
                        annot = page.add_highlight_annot(rect)
                        annot.set_info(content=f"{issue['code']} - {issue['explanation']}")
                    label_rect = rects[0]
                    x = label_rect.x0 - 24 if label_rect.x0 > 42 else min(label_rect.x1 + 4, page.rect.width - 34)
                    point = fitz.Point(x, min(max(label_rect.y0 + 7, 14), page.rect.height - 18))
                    page.insert_text(point, issue["code"], fontsize=7.5, color=(0.55, 0, 0))
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
        path = self.base_dir / "storage" / "tmp" / output_name(document_id, "anexo_apontamentos", "pdf")
        c = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        y = height - 50
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, "Conferência Documento - Anexo do PDF grifado")
        y -= 24
        c.setFont("Helvetica", 9)
        if document:
            y = self._draw_line(c, y, f"Documento: {document['original_filename']}", height)
            y = self._draw_line(c, y, f"Tipo estimado: {document['document_type'] or '-'}", height)
            y = self._draw_line(c, y, f"Empresa identificada: {document['company_name'] or '-'}", height)
        if totals:
            y = self._draw_line(
                c,
                y,
                f"Total: {totals['total']} | Baixa: {totals['BAIXA']} | Média: {totals['MEDIA']} | Alta: {totals['ALTA']} | Crítica: {totals['CRITICA']} | Conferir: {totals['CONFERIR']}",
                height,
            )
        c.setFont("Helvetica-Oblique", 8)
        y = self._draw_line(c, y - 4, "A versão final exige revisão humana. Este sistema não substitui avaliação jurídica profissional.", height)
        y -= 14
        c.setFont("Helvetica", 9)
        for issue in issues:
            lines = [
                f"{issue['code']} | Página: {issue.get('page_number') or '-'} | {issue['issue_type']} | {issue['severity']} | Fonte: {self._source_label(issue.get('source'))}",
                f"Trecho: {issue.get('original_text') or '-'}",
                f"Explicação: {issue.get('explanation') or '-'}",
                f"Sugestão: {issue.get('suggestion') or '-'}",
                f"Justificativa técnica: {issue.get('technical_reason') or '-'}",
                f"Ação: {issue.get('recommended_action') or '-'}",
            ]
            if issue.get("repeated_group_id"):
                lines.extend([
                    "Ocorrência repetida: sim",
                    f"Grupo: {issue.get('repeated_group_id')} ({issue.get('repeated_count') or 0} ocorrências)",
                ])
            for line in lines:
                y = self._draw_line(c, y, line, height)
            y -= 8
        c.save()
        return path

    def _append_pdf(self, base, appendix):
        with fitz.open(base) as doc, fitz.open(appendix) as extra:
            doc.insert_pdf(extra)
            doc.saveIncr()

    def _draw_line(self, c, y, text, height):
        for chunk in self._wrap(text, 112):
            if y < 55:
                c.showPage()
                c.setFont("Helvetica", 9)
                y = height - 50
            c.drawString(50, y, chunk)
            y -= 13
        return y

    def _wrap(self, text, size):
        words = str(text or "").split()
        if not words:
            return [""]
        lines = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) <= size:
                current = candidate
                continue
            if current:
                lines.append(current)
            current = word
        if current:
            lines.append(current)
        return lines

    def _source_label(self, source):
        return {"BOTH": "Regra + IA", "RULE": "Regra", "AI": "IA"}.get(source or "", source or "-")
