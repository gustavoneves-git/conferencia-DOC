import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def safe_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_") or "documento"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stamp}_{uuid4().hex[:8]}_{stem}{suffix}"


def output_name(document_id: int, label: str, suffix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"doc_{document_id}_{label}_{stamp}.{suffix.lstrip('.')}"
