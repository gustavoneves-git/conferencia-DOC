from dataclasses import dataclass


@dataclass
class ReviewSession:
    id: int
    document_id: int
    status: str
    total_issues: int
