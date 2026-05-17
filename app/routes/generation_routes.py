from flask import Blueprint, abort, current_app, render_template, request, send_file

from app.document_types.catalog import get_document_type, get_types_for_creation_menu
from app.services.ltda_generation_service import LtdaGenerationService

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


@bp.get("/ltda/constituicao")
def ltda_constituicao_form():
    return render_template("ltda_constituicao_form.html")


@bp.post("/ltda/constituicao/generate")
def ltda_constituicao_generate():
    result = LtdaGenerationService().generate_constituicao(request.form.to_dict(flat=True))
    return render_template("ltda_generation_result.html", result=result)


@bp.get("/generated/download")
def download_generated():
    path = request.args.get("path")
    if not path:
        abort(404)
    from pathlib import Path

    file_path = Path(path)
    base = current_app.config["BASE_DIR"] / "storage" / "generated"
    try:
        file_path.resolve().relative_to(base.resolve())
    except ValueError:
        abort(403)
    if not file_path.exists():
        abort(404)
    return send_file(file_path, as_attachment=True)
