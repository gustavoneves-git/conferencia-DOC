import json
import re

from app.models.constants import ISSUE_TYPES, SEVERITIES


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Resposta da IA vazia.")
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("Resposta da IA nao contem JSON.")
        return json.loads(match.group(0))


def _norm_enum(value: str, allowed: set[str], fallback: str) -> str:
    normalized = (value or "").upper().strip().replace("Á", "A").replace("É", "E").replace("Í", "I")
    normalized = normalized.replace("Ó", "O").replace("Ú", "U").replace("Ç", "C").replace(" ", "_")
    return normalized if normalized in allowed else fallback


def normalize_issue(issue: dict, index: int) -> dict:
    severity = _norm_enum(issue.get("gravidade") or issue.get("severity"), SEVERITIES, "MEDIA")
    issue_type = _norm_enum(issue.get("tipo") or issue.get("issue_type"), ISSUE_TYPES, "OUTRO")
    if issue_type == "DADO_A_CONFERIR":
        severity = "CONFERIR"
    return {
        "code": f"E{index:03d}",
        "page_number": issue.get("pagina_estimada") or issue.get("page_number"),
        "original_text": issue.get("trecho_original") or issue.get("original_text") or "",
        "issue_type": issue_type,
        "severity": severity,
        "explanation": issue.get("explicacao") or issue.get("explanation") or "",
        "technical_reason": issue.get("justificativa_tecnica") or issue.get("technical_reason") or "",
        "suggestion": issue.get("sugestao") or issue.get("suggestion") or "",
        "recommended_action": issue.get("acao_recomendada") or issue.get("recommended_action") or "Revisar o apontamento.",
        "can_be_highlighted": bool(issue.get("pode_ser_grifado", issue.get("can_be_highlighted", True))),
        "located_in_pdf": bool(issue.get("located_in_pdf", False)),
        "source": issue.get("source", "AI"),
        "status": issue.get("status", "OPEN"),
    }


def validate_review_payload(payload: dict) -> dict:
    apontamentos = payload.get("apontamentos")
    if apontamentos is None:
        raise ValueError("Payload sem apontamentos.")
    normalized = [normalize_issue(item, idx) for idx, item in enumerate(apontamentos, start=1)]
    summary = {"total": len(normalized), "BAIXA": 0, "MEDIA": 0, "ALTA": 0, "CRITICA": 0, "CONFERIR": 0}
    for issue in normalized:
        summary[issue["severity"]] += 1
    payload["normalized_issues"] = normalized
    payload["normalized_summary"] = summary
    return payload
