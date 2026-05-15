import pytest

from app.ai.json_guard import extract_json, validate_review_payload


def test_extract_json_with_text_around():
    payload = extract_json('texto {"apontamentos": []} fim')
    assert payload["apontamentos"] == []


def test_validate_normalizes_issue():
    payload = validate_review_payload({"apontamentos": [{"tipo": "ortografia", "gravidade": "baixa"}]})
    issue = payload["normalized_issues"][0]
    assert issue["code"] == "E001"
    assert issue["issue_type"] == "ORTOGRAFIA"
    assert issue["severity"] == "BAIXA"
