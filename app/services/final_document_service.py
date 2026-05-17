import json
from pathlib import Path

from docx import Document as DocxDocument
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
            raise ValueError("A versão final exige confirmação humana.")
        docs = DocumentRepository()
        reviews = ReviewRepository()
        files = GeneratedFileRepository()
        document = docs.get(document_id)
        corrected_file = files.latest_for_session(document_id, session_id, "DOCX_CORRIGIDO")
        corrected_pdf = files.latest_for_session(document_id, session_id, "PDF_CORRIGIDO")
        if not corrected_file and not corrected_pdf:
            raise ValueError("Gere o documento corrigido para revisão antes da versão final.")
        corrected_text = self._load_corrected_text(document_id, session_id, corrected_file)
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
        text = self._strip_internal_notes(
            self._protect_pending_human_checks(corrected_text, data.get("texto_final") or corrected_text, issues)
        )
        base = current_app.config["BASE_DIR"]
        docx = base / "storage" / "final" / output_name(document_id, "final", "docx", document["original_filename"])
        pdf = base / "storage" / "final" / output_name(document_id, "final", "pdf", document["original_filename"])
        writer = DocxOutputService()
        company = data.get("empresa") or document["company_name"]
        writer.create_docx(str(docx), title, text, company)
        writer.create_pdf(str(pdf), title, text, company)
        files.create(document_id, session_id, "DOCX_FINAL", str(docx))
        files.create(document_id, session_id, "PDF_FINAL", str(pdf))
        docs.update_status(document_id, "FINAL_PARA_PROTOCOLO")
        return str(docx), str(pdf)

    def _load_corrected_text(self, document_id: int, session_id: int, corrected_file=None) -> str:
        files = GeneratedFileRepository()
        audit = files.latest_for_session(document_id, session_id, "JSON_CORRECOES_APLICADAS")
        docs = DocumentRepository()
        pages = docs.pages(document_id)
        original_text = "\n".join(row["extracted_text"] for row in pages)
        if corrected_file and Path(corrected_file["path"]).exists():
            try:
                doc = DocxDocument(corrected_file["path"])
                text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                if text.strip():
                    return text
            except Exception:
                pass
        if audit and Path(audit["path"]).exists():
            try:
                data = json.loads(Path(audit["path"]).read_text(encoding="utf-8"))
                # O JSON de auditoria não armazena o texto integral para reduzir duplicação de dados sensíveis.
                corrected = original_text
                for correction in data.get("correcoes_aplicadas", []):
                    original = correction.get("trecho_original") or ""
                    replacement = correction.get("trecho_corrigido") or ""
                    if original and replacement:
                        corrected = corrected.replace(original, replacement, 1)
                return corrected
            except (OSError, json.JSONDecodeError):
                return original_text
        return original_text

    def _strip_internal_notes(self, text: str) -> str:
        blocked = ("alerta interno", "observação interna", "observacao interna", "ia:", "inteligência artificial")
        clean_lines = []
        for line in (text or "").splitlines():
            lower = line.strip().lower()
            if any(term in lower for term in blocked):
                continue
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()

    def _protect_pending_human_checks(self, corrected_text: str, final_text: str, issues) -> str:
        result = final_text
        for issue in issues:
            if not self._requires_human_preservation(issue):
                continue
            original = (issue.get("original_text") or "").strip()
            suggestion = (issue.get("suggestion") or "").strip()
            if not original or original not in corrected_text:
                continue
            if suggestion and suggestion in result:
                result = result.replace(suggestion, original, 1)
                continue
            if original in result:
                continue
            # A IA reescreveu ou removeu um ponto que dependia de validação humana.
            # Nessa situação, a versão corrigida é a fonte mais segura para o final.
            return corrected_text
        return result

    def _requires_human_preservation(self, issue) -> bool:
        severity = (issue.get("severity") or "").upper()
        issue_type = (issue.get("issue_type") or "").upper()
        return severity == "CONFERIR" or issue_type in {"DADO_A_CONFERIR", "CLAUSULA_JURIDICA_SENSIVEL"}
