from app.services.text_match_service import locate_strategy


class PdfLocatorService:
    def mark_locations(self, issues, pages):
        page_text = {p["page_number"]: p["text"] for p in pages}
        for issue in issues:
            trecho = (issue.get("original_text") or "").strip()
            page = issue.get("page_number")
            if not trecho:
                issue["located_in_pdf"] = False
                issue["location_strategy"] = "NOT_FOUND"
                continue
            if page in page_text:
                strategy = locate_strategy(page_text[page], trecho)
                if strategy != "NOT_FOUND":
                    issue["located_in_pdf"] = True
                    issue["location_strategy"] = strategy
                    continue
            for text in page_text.values():
                strategy = locate_strategy(text, trecho)
                if strategy != "NOT_FOUND":
                    issue["located_in_pdf"] = True
                    issue["location_strategy"] = strategy
                    break
            else:
                issue["located_in_pdf"] = False
                issue["location_strategy"] = "NOT_FOUND"
        return issues
