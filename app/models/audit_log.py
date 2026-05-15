from dataclasses import dataclass


@dataclass
class AuditLog:
    entity_type: str
    entity_id: int
    action: str
    description: str
