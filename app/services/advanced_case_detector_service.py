from app.services.ltda_generation_validation_service import LtdaGenerationValidationService


def detect_advanced_case(payload: dict) -> dict:
    reasons = []
    socios = payload.get("socios", [])
    capital = payload.get("capital", {})
    administracao = payload.get("administracao", {})
    clausulas = payload.get("clausulas_sensiveis", {})
    empresa = payload.get("empresa", {})

    for index, socio in enumerate(socios, start=1):
        label = socio.get("nome_completo") or f"Sócio {index}"
        if socio.get("tipo_pessoa") == "PJ":
            reasons.append(_reason("SOCIO_PJ", "Sócio pessoa jurídica", f"{label} foi marcado como pessoa jurídica."))
        if socio.get("estrangeiro"):
            reasons.append(_reason("SOCIO_ESTRANGEIRO", "Sócio estrangeiro", f"{label} foi marcado como estrangeiro."))
        if socio.get("menor_idade"):
            reasons.append(_reason("SOCIO_MENOR", "Sócio menor de idade", f"{label} foi marcado como menor de idade."))
        if socio.get("incapaz"):
            reasons.append(_reason("SOCIO_INCAPAZ", "Sócio incapaz", f"{label} foi marcado como incapaz."))

    socios_names = {socio.get("nome_completo", "").casefold() for socio in socios}
    admin = (administracao.get("administrador_nome") or "").casefold()
    if admin and admin not in socios_names:
        reasons.append(_reason("ADMINISTRADOR_NAO_SOCIO", "Administrador não sócio", "O administrador informado não está na lista de sócios."))
    if administracao.get("tipo_administracao") == "conjunta":
        reasons.append(_reason("ADMINISTRACAO_CONJUNTA", "Administração conjunta", "O modelo padrão contempla apenas administração isolada."))

    sensitive_map = {
        "lucros_desproporcionais": ("LUCROS_DESPROPORCIONAIS", "Lucros desproporcionais"),
        "incomunicabilidade": ("INCOMUNICABILIDADE", "Cláusula de incomunicabilidade"),
        "impenhorabilidade": ("IMPENHORABILIDADE", "Cláusula de impenhorabilidade"),
        "regencia_supletiva_sa": ("REGENCIA_SA", "Regência supletiva pela Lei das S/A"),
        "capital_em_bens": ("CAPITAL_EM_BENS", "Capital integralizado com bens"),
        "filial_constituicao": ("FILIAL_CONSTITUICAO", "Filial na constituição"),
    }
    for field, (code, label) in sensitive_map.items():
        if clausulas.get(field):
            reasons.append(_reason(code, label, "Item sensível marcado no formulário."))

    objeto = (empresa.get("objeto_social") or "").strip()
    if not objeto or len(objeto) < 20:
        reasons.append(_reason("OBJETO_GENERICO", "Objeto social ausente ou muito genérico", "Objeto social deve ser específico para geração padrão."))
    if any(term in objeto.casefold() for term in ["financeira", "saúde", "medic", "segurança", "transporte aéreo", "banco"]):
        reasons.append(_reason("ATIVIDADE_REGULADA", "Atividade regulada", "O objeto social indica possível atividade regulada."))

    validation = LtdaGenerationValidationService().validate(payload)
    if validation["errors"]:
        reasons.append(
            _reason(
                "DADOS_OBRIGATORIOS_AUSENTES",
                "Dados obrigatórios ausentes ou inválidos",
                "Há erros de validação que impedem a geração padrão.",
                "ALTA",
            )
        )
    if capital.get("capital_social", 0) <= 0:
        reasons.append(_reason("CAPITAL_INVALIDO", "Capital com valor inválido", "Capital social deve ser maior que zero."))
    quotas_sum = sum(int(socio.get("quotas") or 0) for socio in socios)
    if capital.get("quotas_totais") and quotas_sum != capital.get("quotas_totais"):
        reasons.append(_reason("QUOTAS_DIVERGENTES", "Divergência de quotas", "Soma das quotas não confere com o total informado."))

    return {
        "is_advanced": bool(reasons),
        "advanced_reasons": _dedupe(reasons),
        "recommended_action": (
            "Caso avançado. Geração automática padrão bloqueada. Encaminhar para revisão especializada ou aguardar módulo avançado."
            if reasons
            else "Caso compatível com o modelo padrão."
        ),
    }


def _reason(code, label, description, severity="ALTA"):
    return {"code": code, "label": label, "description": description, "severity": severity}


def _dedupe(reasons):
    seen = set()
    unique = []
    for item in reasons:
        if item["code"] in seen:
            continue
        seen.add(item["code"])
        unique.append(item)
    return unique
