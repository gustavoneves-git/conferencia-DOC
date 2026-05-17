from flask import Blueprint, redirect, render_template, url_for

from app.repositories.document_repository import DocumentRepository
from app.repositories.generated_file_repository import GeneratedFileRepository
from app.repositories.review_repository import ReviewRepository
from app.services.corrected_document_service import CorrectedDocumentService

bp = Blueprint("reviews", __name__, url_prefix="/reviews")


@bp.get("/<int:document_id>/<int:session_id>")
def detail(document_id, session_id):
    docs = DocumentRepository()
    reviews = ReviewRepository()
    files = GeneratedFileRepository()
    issues = reviews.issues(session_id)
    generated_files = files.list_for_document(document_id)
    return render_template(
        "review_detail.html",
        document=docs.get(document_id),
        session=reviews.get_session(session_id),
        issues=issues,
        metrics=_metrics(issues),
        files=generated_files,
        file_status=_file_status(generated_files),
    )


@bp.post("/<int:document_id>/<int:session_id>/corrected")
def generate_corrected(document_id, session_id):
    CorrectedDocumentService().generate(document_id, session_id)
    return redirect(url_for("reviews.detail", document_id=document_id, session_id=session_id))


@bp.get("/<int:document_id>/<int:session_id>/final-confirmation")
def final_confirmation(document_id, session_id):
    docs = DocumentRepository()
    files = GeneratedFileRepository()
    generated_files = files.list_for_document(document_id)
    return render_template(
        "final_confirmation.html",
        document=docs.get(document_id),
        session_id=session_id,
        file_status=_file_status(generated_files),
    )


def _metrics(issues):
    rows = [dict(issue) for issue in issues]
    rule = sum(1 for issue in rows if issue.get("source") == "RULE")
    ai = sum(1 for issue in rows if issue.get("source") == "AI")
    both = sum(1 for issue in rows if issue.get("source") == "BOTH")
    return {
        "located": sum(1 for issue in rows if issue.get("located_in_pdf")),
        "not_located": sum(1 for issue in rows if not issue.get("located_in_pdf")),
        "rule": rule,
        "ai": ai,
        "both": both,
        "rule_total": rule + both,
        "ai_total": ai + both,
    }


def _file_status(files):
    types = {file["file_type"] for file in files}
    return {
        "has_corrected_docx": "DOCX_CORRIGIDO" in types,
        "has_corrected_pdf": "PDF_CORRIGIDO" in types,
        "has_corrected": bool({"DOCX_CORRIGIDO", "PDF_CORRIGIDO"} & types),
        "has_final_docx": "DOCX_FINAL" in types,
        "has_final_pdf": "PDF_FINAL" in types,
        "has_final": bool({"DOCX_FINAL", "PDF_FINAL"} & types),
    }
