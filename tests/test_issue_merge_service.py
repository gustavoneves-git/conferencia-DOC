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


def test_merge_keeps_mandado_judicial_as_own_issue_when_ai_uses_long_sentence():
    rule = {
        "page_number": 2,
        "original_text": "mandado judicial",
        "issue_type": "PADRONIZACAO",
        "severity": "CONFERIR",
        "explanation": "Pode haver troca por mandato.",
        "technical_reason": "Contexto de procuração.",
        "suggestion": "mandato judicial",
        "recommended_action": "Conferir.",
    }
    ai_payload = {
        "normalized_issues": [
            {
                "code": "E001",
                "page_number": 2,
                "original_text": "Faculta-se ao sócio administrador, constituir procuradores em nome da sociedade, no caso de mandado judicial, por prazo indeterminado.",
                "issue_type": "PONTUACAO",
                "severity": "MEDIA",
                "explanation": "Pontuação extensa.",
                "technical_reason": "A frase pode ser melhor pontuada.",
                "suggestion": "Revisar pontuação.",
                "recommended_action": "Revisar.",
                "source": "AI",
            }
        ]
    }
    merged = IssueMergeService().merge(ai_payload, [rule])
    originals = {item["original_text"] for item in merged}
    assert "mandado judicial" in originals
    assert len(merged) == 2


def test_repetition_on_different_pages_is_marked_not_removed():
    rule_issues = [
        {
            "page_number": 3,
            "original_text": "contas-corrente",
            "issue_type": "PADRONIZACAO",
            "severity": "CONFERIR",
            "explanation": "Verificar plural.",
            "technical_reason": "Mesmo termo.",
            "suggestion": "contas-correntes",
            "recommended_action": "Conferir.",
        },
        {
            "page_number": 7,
            "original_text": "contas-corrente",
            "issue_type": "PADRONIZACAO",
            "severity": "CONFERIR",
            "explanation": "Verificar plural.",
            "technical_reason": "Mesmo termo.",
            "suggestion": "contas-correntes",
            "recommended_action": "Conferir.",
        },
    ]
    merged = IssueMergeService().merge({"normalized_issues": []}, rule_issues)
    assert len(merged) == 2
    assert {item["repeated_group_id"] for item in merged} == {"R001"}
    assert {item["repeated_count"] for item in merged} == {2}


def test_merge_does_not_conflate_masculine_and_feminine_property_regime():
    rule_issues = [
        {
            "page_number": 1,
            "original_text": "casado no regime comunhão parcial de bens",
            "issue_type": "REDACAO_FRACA",
            "severity": "MEDIA",
            "explanation": "Falta preposição.",
            "technical_reason": "Regime de bens.",
            "suggestion": "casado sob o regime da comunhão parcial de bens",
            "recommended_action": "Corrigir.",
        },
        {
            "page_number": 1,
            "original_text": "casada no regime comunhão parcial de bens",
            "issue_type": "REDACAO_FRACA",
            "severity": "MEDIA",
            "explanation": "Falta preposição.",
            "technical_reason": "Regime de bens.",
            "suggestion": "casada sob o regime da comunhão parcial de bens",
            "recommended_action": "Corrigir.",
        },
    ]
    merged = IssueMergeService().merge({"normalized_issues": []}, rule_issues)
    originals = {item["original_text"] for item in merged}
    assert "casado no regime comunhão parcial de bens" in originals
    assert "casada no regime comunhão parcial de bens" in originals
