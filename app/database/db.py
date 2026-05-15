import sqlite3
from pathlib import Path

from flask import current_app, g


def _db_path() -> Path:
    url = current_app.config["DATABASE_URL"]
    if not url.startswith("sqlite:///"):
        raise RuntimeError("Apenas DATABASE_URL sqlite:/// e suportado na V1.")
    return current_app.config["BASE_DIR"] / url.replace("sqlite:///", "", 1)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        path = _db_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


def close_db(_error=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app) -> None:
    with app.app_context():
        db = get_db()
        schema = Path(app.config["BASE_DIR"] / "app/database/schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        db.commit()
    app.teardown_appcontext(close_db)
