from flask import Blueprint, render_template

from app.repositories.document_repository import DocumentRepository

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def dashboard():
    repo = DocumentRepository()
    return render_template("dashboard.html", counts=repo.counts(), documents=repo.list_recent(8))
