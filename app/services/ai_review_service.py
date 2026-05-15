import json

from app.ai.client import AIClient
from app.ai.prompt_loader import PromptLoader


class AIReviewService:
    def review(self, pages, metadata, rule_issues):
        pages_text = "\n\n".join(f"--- PAGINA {p['page_number']} ---\n{p['text']}" for p in pages)
        prompt = PromptLoader().load(
            "review_existing_document.md",
            {"PAGES_TEXT": pages_text, "METADATA": json.dumps(metadata, ensure_ascii=False, indent=2)},
        )
        return AIClient().review_document(prompt, mock_issues=rule_issues)
