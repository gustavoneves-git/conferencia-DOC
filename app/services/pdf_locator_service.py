class PdfLocatorService:
    def mark_locations(self, issues, pages):
        page_text = {p["page_number"]: p["text"].lower() for p in pages}
        for issue in issues:
            trecho = (issue.get("original_text") or "").lower().strip()
            page = issue.get("page_number")
            issue["located_in_pdf"] = bool(trecho and page in page_text and trecho in page_text[page])
        return issues
