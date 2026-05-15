from app.services.text_match_service import text_contains


class PdfLocatorService:
    def mark_locations(self, issues, pages):
        page_text = {p["page_number"]: p["text"] for p in pages}
        for issue in issues:
            trecho = (issue.get("original_text") or "").strip()
            page = issue.get("page_number")
            if not trecho:
                issue["located_in_pdf"] = False
                continue
            if page in page_text and text_contains(page_text[page], trecho):
                issue["located_in_pdf"] = True
                continue
            issue["located_in_pdf"] = any(text_contains(text, trecho) for text in page_text.values())
        return issues
