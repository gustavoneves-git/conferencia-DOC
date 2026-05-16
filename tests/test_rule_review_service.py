from app.services.rule_review_service import RuleReviewService


def test_detects_inicio_rule():
    issues = RuleReviewService().review([{"page_number": 1, "text": "CLÁUSULA DA INICIO"}])
    assert issues
    assert issues[0]["suggestion"] == "DO INÍCIO"


def test_detects_property_regime_for_masculine_and_feminine():
    text = (
        "LUIS, casado no regime comunhão parcial de bens. "
        "ISABELA, casada no regime comunhão parcial de bens."
    )
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    suggestions = {issue["original_text"].lower(): issue for issue in issues}
    masculine = suggestions["casado no regime comunhão parcial de bens"]
    feminine = suggestions["casada no regime comunhão parcial de bens"]
    assert masculine["suggestion"] == "casado sob o regime da comunhão parcial de bens"
    assert feminine["suggestion"] == "casada sob o regime da comunhão parcial de bens"
    assert masculine["issue_type"] in {"REDACAO_FRACA", "PADRONIZACAO"}
    assert feminine["issue_type"] in {"REDACAO_FRACA", "PADRONIZACAO"}
    assert masculine["severity"] == "MEDIA"
    assert feminine["severity"] == "MEDIA"


def test_mandado_judicial_is_own_rule_issue_with_punctuation_issue():
    text = (
        "Faculta-se ao sócio administrador, constituir procuradores em nome da sociedade, "
        "com poderes para mandato, sendo que, no caso de mandado judicial, poderá ser por prazo indeterminado."
    )
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    originals = {issue["original_text"]: issue for issue in issues}
    assert "Faculta-se ao sócio administrador, constituir" in originals
    assert "mandado judicial" in originals
    assert originals["mandado judicial"]["suggestion"] == "mandato judicial"
    assert originals["mandado judicial"]["severity"] == "CONFERIR"


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


def test_quoren_female_administrator_declaration_is_not_gender_error():
    text = """
    CLÁUSULA SEXTA – DA ADMINISTRAÇÃO DA SOCIEDADE
    A administração da sociedade caberá a Sr.ª CLAUDIA CHRISTINA DE SOUZA.
    CLÁUSULA NONA – DO DESIMPEDIMENTO
    A sócia administradora declara sob as penas da lei.
    """
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    assert not any(issue["original_text"] == "A sócia administradora declara" for issue in issues)


def test_goga_male_administrator_declaration_is_gender_error():
    text = """
    CLÁUSULA SEXTA – DA ADMINISTRAÇÃO DA SOCIEDADE
    A administração da sociedade caberá ao Sr. RENATO OSVALDO AMARAL DE SOUZA.
    CLÁUSULA NONA – DO DESIMPEDIMENTO
    A sócia administradora declara sob as penas da lei.
    """
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    issue = next(issue for issue in issues if issue["original_text"] == "A sócia administradora declara")
    assert issue["severity"] == "ALTA"
    assert issue["suggestion"] == "O sócio administrador declara"


def test_peita_ou_suborno_is_not_rule_error():
    text = "não está condenado por crime de prevaricação, peita ou suborno, concussão ou peculato."
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    assert not issues


def test_female_resident_domiciliado_is_still_detected():
    text = "CLAUDIA CHRISTINA DE SOUZA, brasileira, casada, empresária, residente e domiciliado em Jandira."
    issues = RuleReviewService().review([{"page_number": 1, "text": text}])
    assert any(issue["original_text"] == "domiciliado" and issue["suggestion"] == "domiciliada" for issue in issues)
