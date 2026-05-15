from app.services.issue_merge_service import IssueMergeService


def test_merge_marks_rule_and_ai_duplicate_as_both():
    rule = {
        "page_number": 1,
        "original_text": "O sócio administrador, poderá",
        "issue_type": "PONTUACAO",
        "severity": "MEDIA",
        "explanation": "Regra fixa.",
        "technical_reason": "Virgula indevida.",
        "suggestion": "O sócio administrador poderá",
        "recommended_action": "Corrigir.",
    }
    ai_payload = {
        "normalized_issues": [
            {
                "code": "E001",
                "page_number": 1,
                "original_text": "O socio administrador, podera",
                "issue_type": "PONTUACAO",
                "severity": "ALTA",
                "explanation": "A virgula separa sujeito e verbo.",
                "technical_reason": "Pontuacao prejudica a norma culta.",
                "suggestion": "O sócio administrador poderá",
                "recommended_action": "Remover a virgula.",
                "source": "AI",
            }
        ]
    }
    merged = IssueMergeService().merge(ai_payload, [rule])
    assert len(merged) == 1
    assert merged[0]["source"] == "BOTH"
    assert merged[0]["severity"] == "ALTA"
