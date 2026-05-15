from app.services.rule_review_service import RuleReviewService


def test_detects_inicio_rule():
    issues = RuleReviewService().review([{"page_number": 1, "text": "CLÁUSULA DA INICIO"}])
    assert issues
    assert issues[0]["suggestion"] == "DO INÍCIO"


def test_detects_masculine_qualification_with_feminine_terms():
    text = "GABRIEL VINICIUS, brasileiro, casado, empresário, portadora da cédula, inscrita no CPF, domiciliada em Osasco."
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    suggestions = {issue["original_text"].lower(): issue["suggestion"] for issue in issues if issue["issue_type"] == "ERRO_GENERO"}
    assert suggestions["portadora"] == "portador"
    assert suggestions["inscrita"] == "inscrito"
    assert suggestions["domiciliada"] == "domiciliado"


def test_detects_feminine_qualification_with_masculine_terms():
    text = "MARIA, brasileira, casada, empresária, portador da cédula, inscrito no CPF, domiciliado em Osasco."
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    suggestions = {issue["original_text"].lower(): issue["suggestion"] for issue in issues if issue["issue_type"] == "ERRO_GENERO"}
    assert suggestions["portador"] == "portadora"
    assert suggestions["inscrito"] == "inscrita"
    assert suggestions["domiciliado"] == "domiciliada"


def test_detects_age_jbx_rules():
    text = """
    ORDEM DO DIA: 1°. Saida da diretora.
    Manifestou deixar o Cargo de Diretor e Acionista a Sr.ª BIANCA.
    transferindo de livra e espontânea vontade suas ações que foi aceito por unanimidade.
    Art. 14°. Ao Diretor Presidente compete os poderes.
    poderes da cláusula adjudicia e a extra.
    abrir contas-corrente.
    ordenar títulos de créditos para protesto; k) ordenar títulos de créditos para protesto.
    é consolidado o estatuto social anexo a presente ata.
    """
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    originals = {issue["original_text"] for issue in issues}
    assert "Saida" in originals
    assert "livra e espontânea vontade" in originals
    assert "Cargo de Diretor e Acionista a Sr.ª" in originals
    assert "Ao Diretor Presidente compete os poderes" in originals
    assert "cláusula adjudicia e a extra" in originals
    assert "contas-corrente" in originals
    assert "ordenar títulos de créditos para protesto" in originals
    assert "é consolidado o estatuto social anexo a presente ata" in originals


def test_pesa_clause_has_sensitive_professional_suggestion():
    issues = RuleReviewService().review([{"page_number": 1, "text": "pesa a cláusula restritiva"}])
    issue = issues[0]
    assert issue["issue_type"] == "CLAUSULA_JURIDICA_SENSIVEL"
    assert issue["severity"] == "CONFERIR"
    assert "incidem sobre as quotas" in issue["suggestion"]
