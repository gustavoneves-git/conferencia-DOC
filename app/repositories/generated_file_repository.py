from app.database.db import get_db


class GeneratedFileRepository:
    def create(self, document_id, review_session_id, file_type, path):
        db = get_db()
        cur = db.execute(
            "INSERT INTO generated_files (document_id, review_session_id, file_type, path) VALUES (?, ?, ?, ?)",
            (document_id, review_session_id, file_type, path),
        )
        db.commit()
        return cur.lastrowid

    def list_for_document(self, document_id):
        return get_db().execute(
            "SELECT * FROM generated_files WHERE document_id = ? ORDER BY created_at DESC", (document_id,)
        ).fetchall()

    def get(self, file_id):
        return get_db().execute("SELECT * FROM generated_files WHERE id = ?", (file_id,)).fetchone()
