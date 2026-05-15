from pathlib import Path

from flask import current_app

from app.repositories.document_repository import DocumentRepository
from app.repositories.generated_file_repository import GeneratedFileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.ai_review_service import AIReviewService
from app.services.audit_log_service import AuditLogService
from app.services.document_classifier_service import DocumentClassifierService
from app.services.issue_merge_service import IssueMergeService
from app.services.pdf_annotation_service import PdfAnnotationService
from app.services.pdf_locator_service import PdfLocatorService
from app.services.report_pdf_service import ReportPdfService
from app.services.rule_review_service import RuleReviewService
from app.services.text_extraction_service import TextExtractionService


class ReviewOrchestratorService:
    def run(self, document_id: int) -> int:
        docs = DocumentRepository()
        reviews = ReviewRepository()
        files = GeneratedFileRepository()
        document = docs.get(document_id)
        if not document:
            raise ValueError("Documento nao encontrado.")
        try:
            docs.update_status(document_id, "REVIEWING")
            pages = TextExtractionService().extract_pages(document["original_path"])
            docs.save_pages(document_id, pages)
            classifier = DocumentClassifierService().classify("\n".join(p["text"] for p in pages))
            docs.update_metadata(document_id, classifier["document_type"], classifier["company_name"])
            docs.update_status(document_id, "TEXT_EXTRACTED")

            rule_issues = RuleReviewService().review(pages)
            metadata = {
                "document_type_informado": document["document_type"],
                "document_type_estimado": classifier["document_type"],
                "empresa": classifier["company_name"],
                "arquivo": document["original_filename"],
            }
            ai_payload = AIReviewService().review(pages, metadata, rule_issues)
            issues = IssueMergeService().merge(ai_payload)
            issues = PdfLocatorService().mark_locations(issues, pages)
            totals = self._totals(issues)
            session_id = reviews.create_session(
                document_id,
                "COMPLETED",
                totals,
                current_app.config["AI_MODE"],
                current_app.config["OPENAI_MODEL"],
            )
            reviews.save_issues(session_id, issues)

            refreshed = docs.get(document_id)
            annotated = PdfAnnotationService(current_app.config["BASE_DIR"]).generate(document_id, document["original_path"], issues)
            if annotated:
                files.create(document_id, session_id, "PDF_GRIFADO", annotated)
            report = ReportPdfService(current_app.config["BASE_DIR"]).generate(document_id, refreshed, session_id, issues, totals)
            files.create(document_id, session_id, "RELATORIO_PDF", report)
            docs.update_status(document_id, "ANNOTATED_READY")
            AuditLogService().log("document", document_id, "REVIEW_COMPLETED", "Revisao concluida.")
            return session_id
        except Exception:
            docs.update_status(document_id, "ERROR")
            raise

    def _totals(self, issues):
        totals = {"total": len(issues), "BAIXA": 0, "MEDIA": 0, "ALTA": 0, "CRITICA": 0, "CONFERIR": 0}
        for issue in issues:
            totals[issue["severity"]] = totals.get(issue["severity"], 0) + 1
        return totals
