import json

from flask import current_app

from app.ai.client import AIClient
from app.ai.prompt_loader import PromptLoader
from app.repositories.document_repository import DocumentRepository
from app.repositories.generated_file_repository import GeneratedFileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.docx_output_service import DocxOutputService
from app.services.file_naming_service import output_name


class FinalDocumentService:
    def generate(self, document_id: int, session_id: int, human_confirmed: bool):
        if not human_confirmed:
            raise ValueError("A versao final exige confirmacao humana.")
        docs = DocumentRepository()
        reviews = ReviewRepository()
        files = GeneratedFileRepository()
        document = docs.get(document_id)
        pages = docs.pages(document_id)
        corrected_text = "\n".join(row["extracted_text"] for row in pages)
        issues = [dict(row) for row in reviews.issues(session_id)]
        prompt = PromptLoader().load(
            "generate_final_document.md",
            {
                "CORRECTED_TEXT": corrected_text,
                "APPROVED_CORRECTIONS": json.dumps(issues, ensure_ascii=False, indent=2),
                "DOCUMENT_TYPE": document["document_type"] or "",
            },
        )
        payload = AIClient().generate_json(
            prompt,
            {
                "documento_final": {
                    "tipo_documental": document["document_type"] or "",
                    "empresa": document["company_name"] or "",
                    "titulo": "Documento final para protocolo",
                    "texto_final": corrected_text,
                },
                "observacoes_internas": [],
            },
        )
        data = payload.get("documento_final", {})
        title = data.get("titulo") or "Documento final para protocolo"
        text = data.get("texto_final") or corrected_text
        base = current_app.config["BASE_DIR"]
        docx = base / "storage" / "final" / output_name(document_id, "final", "docx")
        pdf = base / "storage" / "final" / output_name(document_id, "final", "pdf")
        writer = DocxOutputService()
        company = data.get("empresa") or document["company_name"]
        writer.create_docx(str(docx), title, text, company)
        writer.create_pdf(str(pdf), title, text, company)
        files.create(document_id, session_id, "DOCX_FINAL", str(docx))
        files.create(document_id, session_id, "PDF_FINAL", str(pdf))
        docs.update_status(document_id, "FINAL_READY")
        return str(docx), str(pdf)
