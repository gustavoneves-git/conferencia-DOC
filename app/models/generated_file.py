from dataclasses import dataclass


@dataclass
class GeneratedFile:
    id: int
    document_id: int
    review_session_id: int | None
    file_type: str
    path: str
