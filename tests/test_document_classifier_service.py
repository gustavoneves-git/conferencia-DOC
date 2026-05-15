from app.services.document_classifier_service import DocumentClassifierService


def test_identifies_ltda_company_after_contract_title():
    text = """
    CONTRATO SOCIAL DE CONSTITUIÇÃO DE SOCIEDADE LIMITADA
    GOGA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA
    Pelo presente instrumento particular...
    """
    result = DocumentClassifierService().classify(text)
    assert result["company_name"] == "GOGA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA"


def test_does_not_return_contract_title_fragment_as_company():
    text = "CONTRATO SOCIAL DE CONSTITUIÇÃO DE SOCIEDADE LIMITADA\nLUFISA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA"
    result = DocumentClassifierService().classify(text)
    assert result["company_name"] != "O DE SOCIEDADE LIMITADA"
    assert result["company_name"] == "LUFISA EMPREENDIMENTOS E PARTICIPAÇÕES LTDA"


def test_identifies_sa_company_in_age_header():
    text = """
    ATA DA ASSEMBLEIA GERAL EXTRAORDINÁRIA
    JBX CONSTRUÇÃO E EMPREENDIMENTOS COMERCIAIS S/A.
    CNPJ n° 00.000.000/0001-00
    """
    result = DocumentClassifierService().classify(text)
    assert result["document_type"] == "ATA_AGE"
    assert result["company_name"] == "JBX CONSTRUÇÃO E EMPREENDIMENTOS COMERCIAIS S/A."
