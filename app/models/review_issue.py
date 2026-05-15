from dataclasses import dataclass


@dataclass
class ReviewIssue:
    code: str
    page_number: int | None
    original_text: str
    issue_type: str
    severity: str
    explanation: str
    technical_reason: str
    suggestion: str
    recommended_action: str
    can_be_highlighted: bool = True
    located_in_pdf: bool = False
    source: str = "RULE"
    status: str = "OPEN"
