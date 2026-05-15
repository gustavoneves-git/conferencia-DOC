import pytest

from app.ai.json_guard import extract_json, validate_review_payload


def test_extract_json_with_text_around():
    payload = extract_json('texto {"apontamentos": []} fim')
    assert payload["apontamentos"] == []


def test_extract_json_from_ai_response_with_nested_objects():
    payload = extract_json('antes\n{"documento":{},"resumo":{},"apontamentos":[{"tipo":"pontuação"}]}\ndepois')
    assert payload["apontamentos"][0]["tipo"] == "pontuação"


def test_validate_normalizes_issue():
    payload = validate_review_payload({"apontamentos": [{"tipo": "ortografia", "gravidade": "baixa"}]})
    issue = payload["normalized_issues"][0]
    assert issue["code"] == "E001"
    assert issue["issue_type"] == "ORTOGRAFIA"
    assert issue["severity"] == "BAIXA"


def test_validate_handles_missing_apontamentos():
    payload = validate_review_payload({"documento": {}})
    assert payload["normalized_issues"] == []
    assert payload["normalized_summary"]["total"] == 0


def test_validate_dedupes_similar_issues():
    payload = validate_review_payload(
        {
            "apontamentos": [
                {"trecho_original": "O sócio administrador, poderá", "tipo": "PONTUACAO", "gravidade": "MEDIA"},
                {"trecho_original": "O socio administrador, podera", "tipo": "PONTUACAO", "gravidade": "ALTA"},
            ]
        }
    )
    assert len(payload["normalized_issues"]) == 1
    assert payload["normalized_issues"][0]["severity"] == "ALTA"
