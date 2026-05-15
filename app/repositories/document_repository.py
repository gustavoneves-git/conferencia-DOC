from app.database.db import get_db


class DocumentRepository:
    def create(self, original_filename, stored_filename, original_path, document_type=None):
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO documents (original_filename, stored_filename, original_path, document_type)
            VALUES (?, ?, ?, ?)
            """,
            (original_filename, stored_filename, original_path, document_type),
        )
        db.commit()
        return cur.lastrowid

    def get(self, document_id):
        return get_db().execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()

    def list_recent(self, limit=10):
        return get_db().execute(
            "SELECT * FROM documents ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()

    def counts(self):
        db = get_db()
        total = db.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]
        reviewing = db.execute(
            "SELECT COUNT(*) AS n FROM documents WHERE status IN ('UPLOADED','TEXT_EXTRACTED','REVIEWING')"
        ).fetchone()["n"]
        corrected = db.execute("SELECT COUNT(*) AS n FROM documents WHERE status = 'CORRECTED_READY'").fetchone()["n"]
        final = db.execute("SELECT COUNT(*) AS n FROM documents WHERE status = 'FINAL_READY'").fetchone()["n"]
        return {"total": total, "reviewing": reviewing, "corrected": corrected, "final": final}

    def update_status(self, document_id, status):
        db = get_db()
        db.execute("UPDATE documents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, document_id))
        db.commit()

    def update_metadata(self, document_id, document_type=None, company_name=None):
        db = get_db()
        db.execute(
            "UPDATE documents SET document_type = COALESCE(?, document_type), company_name = COALESCE(?, company_name), updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (document_type, company_name, document_id),
        )
        db.commit()

    def save_pages(self, document_id, pages):
        db = get_db()
        db.execute("DELETE FROM document_pages WHERE document_id = ?", (document_id,))
        db.executemany(
            "INSERT INTO document_pages (document_id, page_number, extracted_text) VALUES (?, ?, ?)",
            [(document_id, p["page_number"], p["text"]) for p in pages],
        )
        db.commit()

    def pages(self, document_id):
        return get_db().execute(
            "SELECT * FROM document_pages WHERE document_id = ? ORDER BY page_number", (document_id,)
        ).fetchall()
