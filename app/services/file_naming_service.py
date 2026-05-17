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


def clean_document_name(name: str | None, fallback: str = "documento") -> str:
    stem = Path(name or fallback).stem
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" ._-") or fallback
    return stem[:95].strip(" ._-") or fallback


def output_name(document_id: int, label: str, suffix: str, original_name: str | None = None) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = suffix.lstrip(".")
    labels = {
        "grifado": "grifado",
        "relatorio": "relatorio_tecnico",
        "corrigido": "corrigido_revisao",
        "final": "final_protocolo",
    }
    professional_label = labels.get(label, label)
    if original_name:
        return f"{clean_document_name(original_name)}__{professional_label}__{stamp}.{suffix}"
    return f"doc_{document_id}_{label}_{stamp}.{suffix}"
