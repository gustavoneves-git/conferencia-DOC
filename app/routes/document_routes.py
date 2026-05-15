from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app.services.document_ingestion_service import DocumentIngestionService
from app.services.review_orchestrator_service import ReviewOrchestratorService

bp = Blueprint("documents", __name__, url_prefix="/documents")


@bp.get("/upload")
def upload_form():
    return render_template("upload.html")


@bp.post("/upload")
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Selecione um arquivo PDF ou DOCX.")
        return redirect(url_for("documents.upload_form"))
    try:
        document_id = DocumentIngestionService(current_app.config["BASE_DIR"]).save_upload(
            file, request.form.get("document_type")
        )
        session_id = ReviewOrchestratorService().run(document_id)
        return redirect(url_for("reviews.detail", document_id=document_id, session_id=session_id))
    except Exception as exc:
        flash(str(exc))
        return redirect(url_for("documents.upload_form"))
