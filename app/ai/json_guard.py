import json
import re
import unicodedata
from difflib import SequenceMatcher

from app.models.constants import ISSUE_TYPES, SEVERITIES


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Resposta da IA vazia.")
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        candidate = _balanced_json_object(text)
        if candidate is None:
            raise ValueError("Resposta da IA nao contem JSON valido.")
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON da IA invalido: {exc.msg}.") from exc


def _balanced_json_object(text: str) -> str | None:
    start = text.find("{")
    while start != -1:
        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            char = text[idx]
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
        start = text.find("{", start + 1)
    return None


def _norm_enum(value: str, allowed: set[str], fallback: str) -> str:
    aliases = {
        "MEDIO": "MEDIA",
        "MÉDIA": "MEDIA",
        "CRITICO": "CRITICA",
        "CRÍTICA": "CRITICA",
        "CHECAR": "CONFERIR",
        "VERIFICAR": "CONFERIR",
        "DADO A CONFERIR": "DADO_A_CONFERIR",
        "DADOS_A_CONFERIR": "DADO_A_CONFERIR",
        "ACENTUAÇÃO": "ACENTUACAO",
        "PONTUAÇÃO": "PONTUACAO",
        "FORMATAÇÃO": "FORMATACAO",
        "PADRONIZAÇÃO": "PADRONIZACAO",
        "COERENCIA": "COERENCIA_INTERNA",
        "COERÊNCIA INTERNA": "COERENCIA_INTERNA",
        "ERRO DE GENERO": "ERRO_GENERO",
        "ERRO DE GÊNERO": "ERRO_GENERO",
    }
    raw = str(value or "").upper().strip()
    raw = aliases.get(raw, raw)
    normalized = _strip_accents(raw).replace("-", "_").replace("/", "_")
    normalized = re.sub(r"[^A-Z0-9_]+", "_", normalized).strip("_")
    normalized = aliases.get(normalized, normalized)
    return normalized if normalized in allowed else fallback


def normalize_issue(issue: dict, index: int) -> dict:
    issue = issue or {}
    severity = _norm_enum(issue.get("gravidade") or issue.get("severity"), SEVERITIES, "MEDIA")
    issue_type = _norm_enum(issue.get("tipo") or issue.get("issue_type"), ISSUE_TYPES, "OUTRO")
    if issue_type == "DADO_A_CONFERIR":
        severity = "CONFERIR"
    page_number = issue.get("pagina_estimada") or issue.get("page_number")
    try:
        page_number = int(page_number) if page_number not in ("", None) else None
    except (TypeError, ValueError):
        page_number = None
    return {
        "code": f"E{index:03d}",
        "page_number": page_number,
        "original_text": str(issue.get("trecho_original") or issue.get("original_text") or "").strip(),
        "issue_type": issue_type,
        "severity": severity,
        "explanation": str(issue.get("explicacao") or issue.get("explanation") or "Apontamento identificado para revisão.").strip(),
        "technical_reason": str(issue.get("justificativa_tecnica") or issue.get("technical_reason") or "Revisão técnica recomendada.").strip(),
        "suggestion": str(issue.get("sugestao") or issue.get("suggestion") or "").strip(),
        "recommended_action": str(issue.get("acao_recomendada") or issue.get("recommended_action") or "Revisar o apontamento antes de aplicar qualquer alteração.").strip(),
        "can_be_highlighted": _as_bool(issue.get("pode_ser_grifado", issue.get("can_be_highlighted", True))),
        "located_in_pdf": bool(issue.get("located_in_pdf", False)),
        "source": _norm_source(issue.get("source", "AI")),
        "status": issue.get("status", "OPEN"),
    }


def validate_review_payload(payload: dict) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    apontamentos = payload.get("apontamentos") or []
    if not isinstance(apontamentos, list):
        apontamentos = []
    normalized = [normalize_issue(item, idx) for idx, item in enumerate(apontamentos, start=1)]
    normalized = _dedupe_issues(normalized)
    for idx, issue in enumerate(normalized, start=1):
        issue["code"] = f"E{idx:03d}"
    summary = {"total": len(normalized), "BAIXA": 0, "MEDIA": 0, "ALTA": 0, "CRITICA": 0, "CONFERIR": 0}
    for issue in normalized:
        summary[issue["severity"]] += 1
    payload["normalized_issues"] = normalized
    payload["normalized_summary"] = summary
    payload.setdefault("documento", {})
    payload.setdefault("resumo", {})
    payload.setdefault("versao_corrigida_sugerida", {"observacao": "", "texto_corrigido_integral": ""})
    payload.setdefault("alertas_humanos", [])
    return payload


def _dedupe_issues(issues: list[dict]) -> list[dict]:
    result: list[dict] = []
    for issue in issues:
        if not issue["original_text"] and not issue["explanation"]:
            continue
        duplicate_index = _find_duplicate(result, issue)
        if duplicate_index is None:
            result.append(issue)
            continue
        result[duplicate_index] = _prefer_issue(result[duplicate_index], issue)
    return result


def _find_duplicate(existing: list[dict], issue: dict) -> int | None:
    for idx, candidate in enumerate(existing):
        same_page = candidate.get("page_number") == issue.get("page_number") or not candidate.get("page_number") or not issue.get("page_number")
        same_type = candidate.get("issue_type") == issue.get("issue_type")
        if same_page and same_type and _similar(candidate.get("original_text", ""), issue.get("original_text", "")) >= 0.88:
            return idx
    return None


def _prefer_issue(current: dict, incoming: dict) -> dict:
    current_score = len(current.get("explanation", "")) + len(current.get("technical_reason", ""))
    incoming_score = len(incoming.get("explanation", "")) + len(incoming.get("technical_reason", ""))
    chosen = incoming if incoming_score > current_score else current
    chosen["severity"] = _max_severity(current["severity"], incoming["severity"])
    return chosen


def _similar(left: str, right: str) -> float:
    left_norm = _match_key(left)
    right_norm = _match_key(right)
    if not left_norm or not right_norm:
        return 0
    if left_norm in right_norm or right_norm in left_norm:
        return 1
    return SequenceMatcher(None, left_norm, right_norm).ratio()


def _max_severity(left: str, right: str) -> str:
    order = {"BAIXA": 1, "MEDIA": 2, "CONFERIR": 2, "ALTA": 3, "CRITICA": 4}
    return left if order.get(left, 0) >= order.get(right, 0) else right


def _match_key(text: str) -> str:
    return re.sub(r"\s+", " ", _strip_accents(text).lower()).strip()


def _strip_accents(text: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", str(text or "")) if unicodedata.category(char) != "Mn")


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "nao", "não", "no"}
    return bool(value)


def _norm_source(value: str) -> str:
    source = str(value or "AI").upper().strip()
    return source if source in {"RULE", "AI", "BOTH"} else "AI"
