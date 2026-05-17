from app.generation.ltda_constituicao_schema import UF_VALUES


class LtdaGenerationValidationService:
    def validate(self, payload: dict) -> dict:
        errors = []
        warnings = []
        empresa = payload.get("empresa", {})
        capital = payload.get("capital", {})
        socios = payload.get("socios", [])
        administracao = payload.get("administracao", {})
        sede = empresa.get("endereco_sede", {})

        self._required(errors, "razao_social", empresa.get("razao_social"), "Razão social obrigatória.")
        self._required(errors, "objeto_social", empresa.get("objeto_social"), "Objeto social obrigatório.")
        self._required(errors, "sede_logradouro", sede.get("logradouro"), "Logradouro da sede obrigatório.")
        self._required(errors, "sede_numero", sede.get("numero"), "Número da sede obrigatório.")
        self._required(errors, "sede_bairro", sede.get("bairro"), "Bairro da sede obrigatório.")
        self._required(errors, "sede_cidade", sede.get("cidade"), "Cidade da sede obrigatória.")
        self._required(errors, "sede_cep", sede.get("cep"), "CEP da sede obrigatório.")
        self._required(errors, "data_instrumento", empresa.get("data_instrumento"), "Data do instrumento obrigatória.")
        self._required(errors, "cidade_assinatura", empresa.get("cidade_assinatura"), "Cidade de assinatura obrigatória.")
        self._valid_uf(errors, "sede_uf", sede.get("uf"))
        self._valid_uf(errors, "uf_assinatura", empresa.get("uf_assinatura"))

        if capital.get("capital_social", 0) <= 0:
            errors.append(self._error("capital_social", "Capital social deve ser maior que zero."))
        if capital.get("quotas_totais", 0) <= 0:
            errors.append(self._error("quotas_totais", "Quantidade total de quotas deve ser maior que zero."))
        if capital.get("valor_unitario_quota", 0) <= 0:
            errors.append(self._error("valor_unitario_quota", "Valor unitário da quota deve ser maior que zero."))
        if capital.get("forma_integralizacao") == "futura" and not capital.get("prazo_integralizacao"):
            errors.append(self._error("prazo_integralizacao", "Prazo de integralização obrigatório quando a integralização for futura."))

        if not socios:
            errors.append(self._error("socios", "Informe ao menos um sócio pessoa física."))
        for index, socio in enumerate(socios, start=1):
            prefix = f"socio{index}"
            self._required(errors, f"{prefix}_nome", socio.get("nome_completo"), "Nome do sócio obrigatório.")
            self._required(errors, f"{prefix}_cpf", socio.get("cpf"), "CPF do sócio obrigatório.")
            estado = (socio.get("estado_civil") or "").casefold()
            if estado in {"casado", "casada"} and not socio.get("regime_bens"):
                errors.append(self._error(f"{prefix}_regime_bens", "Regime de bens obrigatório para sócio casado/casada."))

        quotas_sum = sum(int(socio.get("quotas") or 0) for socio in socios)
        if socios and capital.get("quotas_totais") and quotas_sum != capital.get("quotas_totais"):
            errors.append(self._error("quotas", "Soma das quotas dos sócios deve ser igual ao total de quotas."))

        percentages = [float(socio.get("percentual") or 0) for socio in socios if socio.get("percentual")]
        if percentages and abs(sum(percentages) - 100) > 0.05:
            errors.append(self._error("percentual", "Soma dos percentuais informados deve ser 100%."))

        admin = administracao.get("administrador_nome")
        if not admin:
            errors.append(self._error("administrador_nome", "Administrador obrigatório."))
        elif admin.casefold() not in {socio.get("nome_completo", "").casefold() for socio in socios}:
            errors.append(self._error("administrador_nome", "Administrador deve estar na lista de sócios para o modelo padrão."))

        if not empresa.get("foro"):
            warnings.append({"field": "foro", "message": "Foro não informado. Recomenda-se preencher comarca aplicável.", "severity": "WARN"})

        return {"valid": not errors, "errors": errors, "warnings": warnings}

    def _required(self, errors, field, value, message):
        if not str(value or "").strip():
            errors.append(self._error(field, message))

    def _valid_uf(self, errors, field, value):
        if not value or value.upper() not in UF_VALUES:
            errors.append(self._error(field, "UF inválida ou não informada."))

    def _error(self, field, message, severity="ERROR"):
        return {"field": field, "message": message, "severity": severity}
