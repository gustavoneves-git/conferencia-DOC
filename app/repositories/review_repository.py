from app.database.db import get_db


class ReviewRepository:
    def create_session(self, document_id, status, totals, ai_mode, model_used):
        db = get_db()
        cur = db.execute(
            """
            INSERT INTO review_sessions
            (document_id, status, total_issues, total_low, total_medium, total_high, total_critical, total_check, ai_mode, model_used, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                document_id, status, totals["total"], totals["BAIXA"], totals["MEDIA"],
                totals["ALTA"], totals["CRITICA"], totals["CONFERIR"], ai_mode, model_used,
            ),
        )
        db.commit()
        return cur.lastrowid

    def save_issues(self, session_id, issues):
        db = get_db()
        db.executemany(
            """
            INSERT INTO review_issues
            (review_session_id, code, page_number, original_text, issue_type, severity, explanation,
             technical_reason, suggestion, recommended_action, can_be_highlighted, located_in_pdf,
             location_strategy, repeated_group_id, repeated_count, source, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    session_id, i["code"], i.get("page_number"), i.get("original_text", ""),
                    i["issue_type"], i["severity"], i.get("explanation", ""),
                    i.get("technical_reason", ""), i.get("suggestion", ""),
                    i.get("recommended_action", ""), int(i.get("can_be_highlighted", True)),
                    int(i.get("located_in_pdf", False)), i.get("location_strategy"),
                    i.get("repeated_group_id"), int(i.get("repeated_count") or 0),
                    i.get("source", "AI"), i.get("status", "OPEN"),
                )
                for i in issues
            ],
        )
        db.commit()

    def latest_session(self, document_id):
        return get_db().execute(
            "SELECT * FROM review_sessions WHERE document_id = ? ORDER BY id DESC LIMIT 1", (document_id,)
        ).fetchone()

    def get_session(self, session_id):
        return get_db().execute("SELECT * FROM review_sessions WHERE id = ?", (session_id,)).fetchone()

    def issues(self, session_id):
        return get_db().execute(
            "SELECT * FROM review_issues WHERE review_session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
