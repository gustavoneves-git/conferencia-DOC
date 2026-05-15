from pathlib import Path

from werkzeug.datastructures import FileStorage

from app.repositories.document_repository import DocumentRepository
from app.services.file_naming_service import safe_filename


class DocumentIngestionService:
    allowed = {".pdf", ".docx"}

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.repo = DocumentRepository()

    def save_upload(self, file: FileStorage, document_type: str | None = None) -> int:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in self.allowed:
            raise ValueError("Envie um arquivo PDF ou DOCX.")
        stored = safe_filename(file.filename)
        target = self.base_dir / "storage" / "uploads" / stored
        file.save(target)
        return self.repo.create(file.filename, stored, str(target), document_type or None)
