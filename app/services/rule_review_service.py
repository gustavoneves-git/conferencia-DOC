import re


class RuleReviewService:
    def review(self, pages: list[dict]) -> list[dict]:
        issues = []
        full_text = "\n".join(page["text"] for page in pages)
        admin_gender = self._administration_gender(full_text)
        for page in pages:
            text = page["text"]
            page_no = page["page_number"]
            for rule in self._rules():
                for match in re.finditer(rule["pattern"], text, flags=rule.get("flags", re.IGNORECASE)):
                    issues.append(self._issue(page_no, match.group(0), rule))
            issues.extend(self._contextual_gender_issues(page_no, text))
            issues.extend(self._administration_gender_issues(page_no, text, admin_gender))
        return issues

    def _issue(self, page_no, original, rule):
        return {
            "page_number": page_no,
            "original_text": " ".join(original.split()),
            "issue_type": rule["type"],
            "severity": rule["severity"],
            "explanation": rule["explanation"],
            "technical_reason": rule["technical_reason"],
            "suggestion": rule["suggestion"],
            "recommended_action": rule["action"],
            "can_be_highlighted": True,
            "source": "RULE",
        }

    def _rules(self):
        base = lambda p, t, s, e, sug, tr=None, flags=re.IGNORECASE: {
            "pattern": re.escape(p), "type": t, "severity": s, "explanation": e, "flags": flags,
            "suggestion": sug, "technical_reason": tr or e, "action": "Revisar e aplicar a sugestão se confirmada no contexto.",
        }
        regex_rule = lambda p, t, s, e, sug, tr=None, flags=re.IGNORECASE: {
            "pattern": p, "type": t, "severity": s, "explanation": e, "flags": flags,
            "suggestion": sug, "technical_reason": tr or e, "action": "Revisar e aplicar a sugestão se confirmada no contexto.",
        }
        return [
            base("DA INICIO", "ACENTUACAO", "MEDIA", "Título com artigo/acentuação inadequados.", "DO INÍCIO"),
            base("DO INICIO", "ACENTUACAO", "MEDIA", "Falta acento em início.", "DO INÍCIO"),
            base("casado no regime comunhão parcial de bens", "REDACAO_FRACA", "MEDIA", "Falta preposição formal antes do regime.", "casado sob o regime da comunhão parcial de bens"),
            base("casada no regime comunhão parcial de bens", "REDACAO_FRACA", "MEDIA", "Falta preposição formal antes do regime.", "casada sob o regime da comunhão parcial de bens"),
            base("art. 1.072,, § 3º", "PONTUACAO", "ALTA", "Há vírgula duplicada em referência legal.", "art. 1.072, § 3º"),
            base("mandado judicial", "PADRONIZACAO", "CONFERIR", "Em contexto de poderes, pode haver troca por mandato.", "mandato judicial"),
            base("ano calendário", "PADRONIZACAO", "BAIXA", "Termo costuma ser grafado com hífen.", "ano-calendário"),
            base("O sócio administrador, poderá", "PONTUACAO", "MEDIA", "Vírgula indevida entre sujeito e verbo.", "O sócio administrador poderá"),
            base("A sócia administradora, poderá", "PONTUACAO", "MEDIA", "Vírgula indevida entre sujeito e verbo.", "A sócia administradora poderá"),
            base("Faculta-se ao sócio administrador, constituir", "PONTUACAO", "MEDIA", "Vírgula indevida antes do verbo.", "Faculta-se ao sócio administrador constituir"),
            base("Faculta-se a sócia administradora, constituir", "PONTUACAO", "ALTA", "Falta crase e há vírgula indevida.", "Faculta-se à sócia administradora constituir"),
            base("Legislação vigente da época", "REDACAO_FRACA", "BAIXA", "Redação pode ficar mais objetiva e formal.", "legislação vigente à época"),
            base("através de carta", "REDACAO_FRACA", "BAIXA", "Em redação formal, prefira por meio de.", "por meio de carta"),
            base("cabendo aos sócios, os lucros", "PONTUACAO", "MEDIA", "Vírgula separa complemento indevidamente.", "cabendo aos sócios os lucros"),
            base("lucros ou perdas apuradas", "CONCORDANCIA", "MEDIA", "Concordância pode exigir masculino plural.", "lucros ou perdas apurados"),
            base("proporção da sua participação", "CONCORDANCIA", "CONFERIR", "Com sócios no plural, pode ser necessário pluralizar possessivo.", "proporção de suas participações"),
            base(
                "pesa a cláusula restritiva",
                "CLAUSULA_JURIDICA_SENSIVEL",
                "CONFERIR",
                "A redação atual é pouco técnica e deve ser validada pelo responsável, pois envolve restrições sobre quotas/capital social.",
                "incidem sobre as quotas as cláusulas restritivas de incomunicabilidade e impenhorabilidade",
                "A expressão pode comprometer a clareza técnica sobre cláusulas restritivas aplicáveis às quotas.",
            ),
            base(
                "foro da sede",
                "DADO_A_CONFERIR",
                "CONFERIR",
                "A comarca aplicável ao foro deve ser validada conforme a sede e o padrão do ato.",
                "Fica eleito o foro da Comarca de [cidade/UF da sede]...",
                "Se a comarca não puder ser inferida com segurança, validar comarca aplicável.",
            ),
            base("Constituição de Sociedade Limitada", "FORMATACAO", "BAIXA", "Maiúsculas podem ser desnecessárias em texto corrido.", "constituição de sociedade limitada", flags=0),
            base("Balanço Extraordinário", "FORMATACAO", "BAIXA", "Maiúsculas podem ser desnecessárias em texto corrido.", "balanço extraordinário", flags=0),
            base("DIASSIS", "DADO_A_CONFERIR", "CONFERIR", "Nome próprio suspeito deve ser conferido, não corrigido automaticamente.", "conferir grafia do nome"),
            base("sócia falecida", "ERRO_GENERO", "CONFERIR", "Pode indicar gênero inadequado dependendo da pessoa mencionada.", "conferir gênero e qualidade da parte"),
            base("Saida", "ACENTUACAO", "MEDIA", "Falta acento em saída.", "Saída", flags=0),
            base("livra e espontânea vontade", "ORTOGRAFIA", "ALTA", "Há troca de gênero em expressão consagrada.", "livre e espontânea vontade"),
            regex_rule(r"Cargo\s+de\s+Diretor\s+e\s+Acionista\s+a\s+Sr\.ª", "REDACAO_FRACA", "ALTA", "A redação está truncada e prejudica a compreensão da saída da diretora/acionista.", "A Sr.ª ... manifesta sua saída do cargo de Diretora e sua retirada como acionista"),
            base("foi aceito por unanimidade", "CONCORDANCIA", "MEDIA", "A concordância pode estar inadequada em relação ao sujeito anterior da deliberação.", "foi aceita por unanimidade, se o sujeito for transferência/deliberação"),
            base("Ao Diretor Presidente compete os poderes", "CONCORDANCIA", "ALTA", "O verbo deve concordar com o sujeito plural poderes.", "Ao Diretor Presidente competem os poderes"),
            base("cláusula adjudicia e a extra", "DADO_A_CONFERIR", "CONFERIR", "Expressão jurídica provavelmente grafada de forma incorreta.", "cláusula ad judicia et extra"),
            base("contas-corrente", "PADRONIZACAO", "CONFERIR", "Verificar pluralização do termo conforme o contexto.", "contas-correntes"),
            regex_rule(r"é\s+consolidado\s+o\s+estatuto\s+social\s+anexo\s+a\s+presente\s+ata", "REDACAO_FRACA", "MEDIA", "Redação pouco natural e com ausência de crase.", "fica consolidado o estatuto social anexo à presente ata"),
        ]

    def _administration_gender(self, text: str) -> str | None:
        window_match = re.search(
            r"CLÁUSULA\s+SEXTA\s+[–-]\s+DA\s+ADMINISTRAÇÃO\s+DA\s+SOCIEDADE(?P<body>.*?)(?:CLÁUSULA\s+S[ÉE]TIMA|$)",
            text or "",
            flags=re.IGNORECASE | re.DOTALL,
        )
        body = window_match.group("body") if window_match else text or ""
        if re.search(r"\bcaberá\s+ao\s+Sr\.?\b|\bcaberá\s+ao\s+sócio\b", body, flags=re.IGNORECASE):
            return "M"
        if re.search(r"\bcaberá\s+(?:a|à)\s+Sr\.ª\b|\bcaberá\s+(?:a|à)\s+sócia\b", body, flags=re.IGNORECASE):
            return "F"
        if re.search(r"\bsócio\s+administrador\b", body, flags=re.IGNORECASE):
            return "M"
        if re.search(r"\bsócia\s+administradora\b", body, flags=re.IGNORECASE):
            return "F"
        return None

    def _administration_gender_issues(self, page_no: int, text: str, admin_gender: str | None) -> list[dict]:
        issues = []
        if not admin_gender:
            return issues
        if admin_gender == "M" and re.search(r"\bA\s+sócia\s+administradora\s+declara\b", text or "", flags=re.IGNORECASE):
            issues.append(
                {
                    "page_number": page_no,
                    "original_text": "A sócia administradora declara",
                    "issue_type": "ERRO_GENERO",
                    "severity": "ALTA",
                    "explanation": "A cláusula de administração indica administrador masculino, mas o desimpedimento usa forma feminina.",
                    "technical_reason": "A concordância deve acompanhar o administrador nomeado na cláusula de administração.",
                    "suggestion": "O sócio administrador declara",
                    "recommended_action": "Corrigir o gênero após confirmar que a administração foi atribuída a homem.",
                    "can_be_highlighted": True,
                    "source": "RULE",
                }
            )
        if admin_gender == "F" and re.search(r"\bO\s+sócio\s+administrador\s+declara\b", text or "", flags=re.IGNORECASE):
            issues.append(
                {
                    "page_number": page_no,
                    "original_text": "O sócio administrador declara",
                    "issue_type": "ERRO_GENERO",
                    "severity": "ALTA",
                    "explanation": "A cláusula de administração indica administradora feminina, mas o desimpedimento usa forma masculina.",
                    "technical_reason": "A concordância deve acompanhar a administradora nomeada na cláusula de administração.",
                    "suggestion": "A sócia administradora declara",
                    "recommended_action": "Corrigir o gênero após confirmar que a administração foi atribuída a mulher.",
                    "can_be_highlighted": True,
                    "source": "RULE",
                }
            )
        return issues

    def _contextual_gender_issues(self, page_no: int, text: str) -> list[dict]:
        issues = []
        terms = {
            "portadora": "portador",
            "inscrita": "inscrito",
            "domiciliada": "domiciliado",
            "portador": "portadora",
            "inscrito": "inscrita",
            "domiciliado": "domiciliada",
        }
        masculine_context = r"\b(brasileiro|casado|solteiro|divorciado|viúvo|empresário|sócio|administrador)\b"
        feminine_context = r"\b(brasileira|casada|solteira|divorciada|viúva|empresária|sócia|administradora)\b"

        for block in self._qualification_blocks(text):
            context_block = re.sub(r"sociedade\s+empresária(?:\s+limitada)?", "", block, flags=re.IGNORECASE)
            has_masculine = bool(re.search(masculine_context, context_block, flags=re.IGNORECASE))
            has_feminine = bool(re.search(feminine_context, context_block, flags=re.IGNORECASE))
            if not has_masculine and not has_feminine:
                continue
            for term, suggestion in terms.items():
                is_feminine_term = term.endswith("a")
                conflict = (has_masculine and is_feminine_term) or (has_feminine and not is_feminine_term)
                if not conflict:
                    continue
                for match in re.finditer(rf"\b{re.escape(term)}\b", block, flags=re.IGNORECASE):
                    original = match.group(0)
                    issues.append(self._gender_issue(page_no, original, suggestion, has_masculine))
        issues.extend(self._repeated_power_issues(page_no, text))
        issues.extend(self._assembly_accent_issues(page_no, text))
        return issues

    def _qualification_blocks(self, text: str) -> list[str]:
        parts = re.split(r"(?<=[.;])\s+|\n{2,}", text or "")
        return [part for part in parts if re.search(r"\b(portador|portadora|inscrito|inscrita|domiciliado|domiciliada)\b", part, flags=re.IGNORECASE)]

    def _gender_issue(self, page_no: int, original: str, suggestion: str, masculine_context: bool) -> dict:
        explanation = (
            "A qualificação do sócio está no masculino, mas o termo está no feminino."
            if masculine_context
            else "A qualificação da sócia está no feminino, mas o termo está no masculino."
        )
        return {
            "page_number": page_no,
            "original_text": original,
            "issue_type": "ERRO_GENERO",
            "severity": "ALTA",
            "explanation": explanation,
            "technical_reason": "A concordância de gênero deve ser uniforme dentro do bloco de qualificação da pessoa.",
            "suggestion": suggestion,
            "recommended_action": "Corrigir o termo após confirmar a qualificação da pessoa.",
            "can_be_highlighted": True,
            "source": "RULE",
        }

    def _repeated_power_issues(self, page_no: int, text: str) -> list[dict]:
        phrase = "ordenar títulos de créditos para protesto"
        pattern = r"ordenar\s+títulos\s+de\s+créditos\s+para\s+protesto"
        if len(re.findall(pattern, text or "", flags=re.IGNORECASE)) < 2:
            return []
        return [
            {
                "page_number": page_no,
                "original_text": phrase,
                "issue_type": "COERENCIA_INTERNA",
                "severity": "CONFERIR",
                "explanation": "O mesmo poder aparece repetido na lista de atribuições.",
                "technical_reason": "Repetição de poderes pode indicar colagem ou adaptação incompleta de modelo.",
                "suggestion": "remover duplicidade ou consolidar a redação do poder",
                "recommended_action": "Conferir se a repetição é intencional antes de ajustar o estatuto.",
                "can_be_highlighted": True,
                "source": "RULE",
            }
        ]

    def _assembly_accent_issues(self, page_no: int, text: str) -> list[dict]:
        if "ASSEMBLÉIA" not in (text or "") or "Assembleia" not in (text or ""):
            return []
        return [
            {
                "page_number": page_no,
                "original_text": "ASSEMBLÉIA",
                "issue_type": "PADRONIZACAO",
                "severity": "BAIXA",
                "explanation": "Há inconsistência de grafia entre Assembleia e Assembléia no mesmo documento.",
                "technical_reason": "O padrão ortográfico atual recomenda Assembleia, sem acento.",
                "suggestion": "ASSEMBLEIA",
                "recommended_action": "Padronizar a grafia conforme o padrão adotado no documento.",
                "can_be_highlighted": True,
                "source": "RULE",
            }
        ]
