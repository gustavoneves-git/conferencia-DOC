from app.database.db import get_db


class AuditLogService:
    def log(self, entity_type, entity_id, action, description=""):
        db = get_db()
        db.execute(
            "INSERT INTO audit_logs (entity_type, entity_id, action, description) VALUES (?, ?, ?, ?)",
            (entity_type, entity_id, action, description),
        )
        db.commit()
