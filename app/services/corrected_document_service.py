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
                "correcoes_aplicadas": self._corrections_from_issues(issues),
                "alertas": self._alerts_from_issues(issues),
            },
        )
        data = payload.get("documento_corrigido", {})
        title = data.get("titulo") or "Documento corrigido para revisão"
        text = self._restore_protected_text(original_text, data.get("texto_corrigido") or fallback_text, issues)
        base = current_app.config["BASE_DIR"]
        docx = base / "storage" / "corrected" / output_name(document_id, "corrigido", "docx", document["original_filename"])
        pdf = base / "storage" / "corrected" / output_name(document_id, "corrigido", "pdf", document["original_filename"])
        writer = DocxOutputService()
        company = data.get("empresa") or document["company_name"]
        writer.create_docx(str(docx), title, text, company)
        writer.create_pdf(str(pdf), title, text, company)
        audit_path = base / "storage" / "corrected" / output_name(document_id, "corrigido_auditoria", "json", document["original_filename"])
        audit_path.write_text(
            json.dumps(
                {
                    "document_id": document_id,
                    "review_session_id": session_id,
                    "status_saida": "CORRIGIDO_PARA_REVISAO",
                    "correcoes_aplicadas": self._safe_payload_corrections(
                        payload.get("correcoes_aplicadas") or self._corrections_from_issues(issues),
                        issues,
                    ),
                    "alertas": payload.get("alertas") or self._alerts_from_issues(issues),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        files.create(document_id, session_id, "DOCX_CORRIGIDO", str(docx))
        files.create(document_id, session_id, "PDF_CORRIGIDO", str(pdf))
        files.create(document_id, session_id, "JSON_CORRECOES_APLICADAS", str(audit_path))
        docs.update_status(document_id, "CORRIGIDO_PARA_REVISAO")
        return str(docx), str(pdf)

    def _apply_simple_replacements(self, text, issues):
        result = text
        for issue in issues:
            original = issue.get("original_text") or ""
            suggestion = issue.get("suggestion") or ""
            if self._can_apply_automatically(issue) and original and suggestion:
                result = result.replace(original, suggestion, 1)
        return result

    def _can_apply_automatically(self, issue) -> bool:
        severity = (issue.get("severity") or "").upper()
        issue_type = (issue.get("issue_type") or "").upper()
        suggestion = (issue.get("suggestion") or "").strip()
        original = (issue.get("original_text") or "").strip()
        if not original or not suggestion:
            return False
        if severity in {"CONFERIR", "CRITICA"}:
            return False
        if issue_type in {"DADO_A_CONFERIR", "CLAUSULA_JURIDICA_SENSIVEL"}:
            return False
        return True

    def _corrections_from_issues(self, issues):
        corrections = []
        for issue in issues:
            if not self._can_apply_automatically(issue):
                continue
            corrections.append(
                {
                    "codigo": issue.get("code", ""),
                    "trecho_original": issue.get("original_text", ""),
                    "trecho_corrigido": issue.get("suggestion", ""),
                    "motivo": issue.get("technical_reason") or issue.get("explanation") or "Correção sugerida por apontamento confiável.",
                    "aplicado_automaticamente": True,
                }
            )
        return corrections

    def _alerts_from_issues(self, issues):
        alerts = []
        for issue in issues:
            if self._can_apply_automatically(issue):
                continue
            if (issue.get("severity") or "").upper() == "CONFERIR" or (issue.get("issue_type") or "").upper() in {
                "DADO_A_CONFERIR",
                "CLAUSULA_JURIDICA_SENSIVEL",
            }:
                alerts.append(
                    {
                        "codigo": issue.get("code", ""),
                        "descricao": issue.get("original_text", ""),
                        "motivo": "Mantido no texto para conferência humana antes da versão final.",
                    }
                )
        return alerts

    def _protected_issue_codes(self, issues) -> set[str]:
        return {issue.get("code", "") for issue in issues if not self._can_apply_automatically(issue)}

    def _safe_payload_corrections(self, corrections, issues):
        protected = self._protected_issue_codes(issues)
        return [item for item in (corrections or []) if item.get("codigo") not in protected]

    def _restore_protected_text(self, original_text: str, corrected_text: str, issues) -> str:
        result = corrected_text
        for issue in issues:
            if self._can_apply_automatically(issue):
                continue
            original = (issue.get("original_text") or "").strip()
            suggestion = (issue.get("suggestion") or "").strip()
            if original and original not in result and suggestion and suggestion in result:
                result = result.replace(suggestion, original, 1)
            elif original and original not in result:
                # Falha segura: se a IA reescreveu uma pendência de conferência, preserva o
                # trecho original no fim do parágrafo para revisão humana em vez de perder o dado.
                result = f"{result}\n{original}"
        return result
