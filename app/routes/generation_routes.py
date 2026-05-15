from flask import Blueprint, render_template

bp = Blueprint("generation", __name__, url_prefix="/generation")


@bp.get("/")
def form():
    return render_template("generation_form.html")
