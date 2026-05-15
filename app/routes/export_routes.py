from pathlib import Path

from flask import Blueprint, abort, redirect, request, send_file, url_for

from app.repositories.generated_file_repository import GeneratedFileRepository
from app.services.final_document_service import FinalDocumentService

bp = Blueprint("exports", __name__, url_prefix="/exports")


@bp.get("/file/<int:file_id>")
def download(file_id):
    file = GeneratedFileRepository().get(file_id)
    if not file or not Path(file["path"]).exists():
        abort(404)
    return send_file(file["path"], as_attachment=True)


@bp.post("/final/<int:document_id>/<int:session_id>")
def generate_final(document_id, session_id):
    confirmed = request.form.get("human_confirmed") == "on"
    FinalDocumentService().generate(document_id, session_id, confirmed)
    return redirect(url_for("reviews.detail", document_id=document_id, session_id=session_id))
