from dataclasses import dataclass


@dataclass
class Document:
    id: int
    original_filename: str
    stored_filename: str
    original_path: str
    document_type: str | None
    company_name: str | None
    status: str
