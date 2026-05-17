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

    def latest_for_session(self, document_id, review_session_id, file_type):
        return get_db().execute(
            """
            SELECT * FROM generated_files
            WHERE document_id = ? AND review_session_id = ? AND file_type = ?
            ORDER BY created_at DESC, id DESC LIMIT 1
            """,
            (document_id, review_session_id, file_type),
        ).fetchone()

    def get(self, file_id):
        return get_db().execute("SELECT * FROM generated_files WHERE id = ?", (file_id,)).fetchone()
