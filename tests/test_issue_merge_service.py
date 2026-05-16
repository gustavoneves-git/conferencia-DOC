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


def test_merge_consolidates_substring_duplicates():
    rule = {
        "page_number": 3,
        "original_text": "proporção da sua participação",
        "issue_type": "CONCORDANCIA",
        "severity": "CONFERIR",
        "explanation": "Regra curta.",
        "technical_reason": "Mesmo problema.",
        "suggestion": "proporção de suas participações",
        "recommended_action": "Revisar.",
    }
    ai_payload = {
        "normalized_issues": [
            {
                "code": "E001",
                "page_number": 3,
                "original_text": "na proporção da sua participação no capital social",
                "issue_type": "CONCORDANCIA",
                "severity": "MEDIA",
                "explanation": "Explicação mais completa.",
                "technical_reason": "O plural dos sócios pede ajuste do possessivo.",
                "suggestion": "na proporção de suas participações no capital social",
                "recommended_action": "Ajustar se o contrato tratar de vários sócios.",
                "source": "AI",
            }
        ]
    }
    merged = IssueMergeService().merge(ai_payload, [rule])
    assert len(merged) == 1
    assert merged[0]["source"] == "BOTH"
    assert "capital social" in merged[0]["original_text"]


def test_merge_consolidates_adjacent_page_boundary_duplicates():
    rule = {
        "page_number": 2,
        "original_text": "A sócia administradora, poderá",
        "issue_type": "PONTUACAO",
        "severity": "MEDIA",
        "explanation": "Vírgula indevida.",
        "technical_reason": "Mesmo problema.",
        "suggestion": "A sócia administradora poderá",
        "recommended_action": "Revisar.",
    }
    ai_payload = {
        "normalized_issues": [
            {
                "code": "E001",
                "page_number": 3,
                "original_text": "A sócia administradora, poderá fixar uma retirada mensal",
                "issue_type": "PONTUACAO",
                "severity": "MEDIA",
                "explanation": "A vírgula separa sujeito e verbo.",
                "technical_reason": "Pontuação indevida.",
                "suggestion": "A sócia administradora poderá fixar uma retirada mensal",
                "recommended_action": "Remover a vírgula.",
                "source": "AI",
            }
        ]
    }
    merged = IssueMergeService().merge(ai_payload, [rule])
    assert len(merged) == 1
    assert merged[0]["source"] == "BOTH"
