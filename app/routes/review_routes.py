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
    return render_template(
        "review_detail.html",
        document=docs.get(document_id),
        session=reviews.get_session(session_id),
        issues=reviews.issues(session_id),
        files=files.list_for_document(document_id),
    )


@bp.post("/<int:document_id>/<int:session_id>/corrected")
def generate_corrected(document_id, session_id):
    CorrectedDocumentService().generate(document_id, session_id)
    return redirect(url_for("reviews.detail", document_id=document_id, session_id=session_id))


@bp.get("/<int:document_id>/<int:session_id>/final-confirmation")
def final_confirmation(document_id, session_id):
    return render_template("final_confirmation.html", document_id=document_id, session_id=session_id)
