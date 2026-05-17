from flask import Blueprint, render_template

from app.document_types.catalog import get_document_type, get_types_for_creation_menu

bp = Blueprint("generation", __name__, url_prefix="/generation")


@bp.get("/")
def form():
    return render_template("generation_form.html", creation_menu=get_types_for_creation_menu())


@bp.get("/type/<code>")
def type_detail(code):
    document_type = get_document_type(code)
    if not document_type:
        return render_template("generation_type_detail.html", document_type=None, code=code), 404
    return render_template("generation_type_detail.html", document_type=document_type, code=code)
