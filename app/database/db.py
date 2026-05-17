import sqlite3
from pathlib import Path

from flask import current_app, g


def _db_path() -> Path:
    url = current_app.config["DATABASE_URL"]
    if not url.startswith("sqlite:///"):
        raise RuntimeError("Apenas DATABASE_URL sqlite:/// e suportado na V1.")
    raw_path = Path(url.replace("sqlite:///", "", 1))
    if raw_path.is_absolute():
        return raw_path
    return current_app.config["BASE_DIR"] / raw_path


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
        schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
        db.executescript(schema)
        _ensure_columns(db)
        db.commit()
    app.teardown_appcontext(close_db)


def _ensure_columns(db: sqlite3.Connection) -> None:
    columns = {row["name"] for row in db.execute("PRAGMA table_info(review_issues)").fetchall()}
    migrations = {
        "location_strategy": "ALTER TABLE review_issues ADD COLUMN location_strategy TEXT",
        "repeated_group_id": "ALTER TABLE review_issues ADD COLUMN repeated_group_id TEXT",
        "repeated_count": "ALTER TABLE review_issues ADD COLUMN repeated_count INTEGER NOT NULL DEFAULT 0",
    }
    for column, sql in migrations.items():
        if column not in columns:
            db.execute(sql)
