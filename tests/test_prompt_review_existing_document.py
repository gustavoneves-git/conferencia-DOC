from pathlib import Path


def test_review_prompt_requires_short_localizable_excerpts():
    prompt = Path("app/ai/prompts/review_existing_document.md").read_text(encoding="utf-8")
    assert "trecho curto, exato e localizável" in prompt
    assert "Evite devolver parágrafos inteiros" in prompt
    assert "Se houver vários erros na mesma frase, separe em apontamentos diferentes" in prompt


def test_review_prompt_has_age_estatuto_proactivity_instructions():
    prompt = Path("app/ai/prompts/review_existing_document.md").read_text(encoding="utf-8")
    assert "coerência entre ordem do dia e deliberações" in prompt
    assert "estatuto consolidado reproduz corretamente" in prompt
    assert "coexistência de endereço antigo e novo" in prompt
