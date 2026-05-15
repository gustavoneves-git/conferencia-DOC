import json

from flask import current_app

from app.ai.client import AIClient
from app.ai.prompt_loader import PromptLoader
from app.repositories.document_repository import DocumentRepository
from app.repositories.generated_file_repository import GeneratedFileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.docx_output_service import DocxOutputService
from app.services.file_naming_service import output_name


class CorrectedDocumentService:
    def generate(self, document_id: int, session_id: int):
        docs = DocumentRepository()
        reviews = ReviewRepository()
        files = GeneratedFileRepository()
        document = docs.get(document_id)
        pages = docs.pages(document_id)
        issues = [dict(row) for row in reviews.issues(session_id)]
        original_text = "\n".join(row["extracted_text"] for row in pages)
        prompt = PromptLoader().load(
            "generate_corrected_document.md",
            {"DOCUMENT_TEXT": original_text, "REVIEW_ISSUES": json.dumps(issues, ensure_ascii=False, indent=2)},
        )
        fallback_text = self._apply_simple_replacements(original_text, issues)
        payload = AIClient().generate_json(
            prompt,
            {
                "documento_corrigido": {
                    "tipo_documental": document["document_type"] or "",
                    "empresa": document["company_name"] or "",
                    "titulo": "Documento corrigido para revisão",
                    "texto_corrigido": fallback_text,
                },
                "alertas": [],
            },
        )
        data = payload.get("documento_corrigido", {})
        title = data.get("titulo") or "Documento corrigido para revisão"
        text = data.get("texto_corrigido") or fallback_text
        base = current_app.config["BASE_DIR"]
        docx = base / "storage" / "corrected" / output_name(document_id, "corrigido", "docx")
        pdf = base / "storage" / "corrected" / output_name(document_id, "corrigido", "pdf")
        writer = DocxOutputService()
        writer.create_docx(str(docx), title, text)
        writer.create_pdf(str(pdf), title, text)
        files.create(document_id, session_id, "DOCX_CORRIGIDO", str(docx))
        files.create(document_id, session_id, "PDF_CORRIGIDO", str(pdf))
        docs.update_status(document_id, "CORRECTED_READY")
        return str(docx), str(pdf)

    def _apply_simple_replacements(self, text, issues):
        result = text
        for issue in issues:
            original = issue.get("original_text") or ""
            suggestion = issue.get("suggestion") or ""
            if original and suggestion and issue.get("severity") != "CONFERIR":
                result = result.replace(original, suggestion, 1)
        return result
