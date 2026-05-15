import re


class RuleReviewService:
    def review(self, pages: list[dict]) -> list[dict]:
        issues = []
        for page in pages:
            text = page["text"]
            page_no = page["page_number"]
            for rule in self._rules():
                for match in re.finditer(rule["pattern"], text, flags=rule.get("flags", re.IGNORECASE)):
                    issues.append(self._issue(page_no, match.group(0), rule))
        return issues

    def _issue(self, page_no, original, rule):
        return {
            "page_number": page_no,
            "original_text": original,
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
        base = lambda p, t, s, e, sug, tr=None: {
            "pattern": re.escape(p), "type": t, "severity": s, "explanation": e,
            "suggestion": sug, "technical_reason": tr or e, "action": "Revisar e aplicar a sugestao se confirmada no contexto.",
        }
        return [
            base("DA INICIO", "ACENTUACAO", "MEDIA", "Titulo com artigo/acentuacao inadequados.", "DO INÍCIO"),
            base("DO INICIO", "ACENTUACAO", "MEDIA", "Falta acento em inicio.", "DO INÍCIO"),
            base("casado no regime comunhão parcial de bens", "REDACAO_FRACA", "MEDIA", "Falta preposicao formal antes do regime.", "casado sob o regime da comunhão parcial de bens"),
            base("casada no regime comunhão parcial de bens", "REDACAO_FRACA", "MEDIA", "Falta preposicao formal antes do regime.", "casada sob o regime da comunhão parcial de bens"),
            base("art. 1.072,, § 3º", "PONTUACAO", "ALTA", "Ha virgula duplicada em referencia legal.", "art. 1.072, § 3º"),
            base("mandado judicial", "PADRONIZACAO", "CONFERIR", "Em contexto de poderes, pode haver troca por mandato.", "mandato judicial"),
            base("ano calendário", "PADRONIZACAO", "BAIXA", "Termo costuma ser grafado com hifen.", "ano-calendário"),
            base("O sócio administrador, poderá", "PONTUACAO", "MEDIA", "Virgula indevida entre sujeito e verbo.", "O sócio administrador poderá"),
            base("A sócia administradora, poderá", "PONTUACAO", "MEDIA", "Virgula indevida entre sujeito e verbo.", "A sócia administradora poderá"),
            base("Faculta-se ao sócio administrador, constituir", "PONTUACAO", "MEDIA", "Virgula indevida antes do verbo.", "Faculta-se ao sócio administrador constituir"),
            base("Faculta-se a sócia administradora, constituir", "PONTUACAO", "ALTA", "Falta crase e ha virgula indevida.", "Faculta-se à sócia administradora constituir"),
            base("Legislação vigente da época", "REDACAO_FRACA", "BAIXA", "Redacao pode ficar mais objetiva e formal.", "legislação vigente à época"),
            base("através de carta", "REDACAO_FRACA", "BAIXA", "Em redação formal, prefira por meio de.", "por meio de carta"),
            base("cabendo aos sócios, os lucros", "PONTUACAO", "MEDIA", "Virgula separa complemento indevidamente.", "cabendo aos sócios os lucros"),
            base("lucros ou perdas apuradas", "CONCORDANCIA", "MEDIA", "Concordancia pode exigir masculino plural.", "lucros ou perdas apurados"),
            base("proporção da sua participação", "CONCORDANCIA", "CONFERIR", "Com socios no plural, pode ser necessario pluralizar possessivo.", "proporção de suas participações"),
            base("pesa a cláusula restritiva", "ORTOGRAFIA", "ALTA", "Possivel troca de pesa por pesa/consta; requer conferencia.", "consta a cláusula restritiva"),
            base("foro da sede", "CLAUSULA_JURIDICA_SENSIVEL", "CONFERIR", "Clausula de foro deve ser validada conforme ato e partes.", "validar foro aplicável"),
            base("Constituição de Sociedade Limitada", "FORMATACAO", "BAIXA", "Maiusculas podem ser desnecessarias em texto corrido.", "constituição de sociedade limitada"),
            base("Balanço Extraordinário", "FORMATACAO", "BAIXA", "Maiusculas podem ser desnecessarias em texto corrido.", "balanço extraordinário"),
            base("DIASSIS", "DADO_A_CONFERIR", "CONFERIR", "Nome proprio suspeito deve ser conferido, nao corrigido automaticamente.", "conferir grafia do nome"),
            base("sócia falecida", "ERRO_GENERO", "CONFERIR", "Pode indicar genero inadequado dependendo da pessoa mencionada.", "conferir genero e qualidade da parte"),
            base("A sócia administradora declara", "ERRO_GENERO", "ALTA", "Pode haver incompatibilidade com administrador masculino.", "O sócio administrador declara"),
            base("portadora", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa feminina.", "conferir gênero da qualificação"),
            base("inscrita", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa feminina.", "conferir gênero da qualificação"),
            base("domiciliada", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa feminina.", "conferir gênero da qualificação"),
            base("portador", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa masculina.", "conferir gênero da qualificação"),
            base("inscrito", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa masculina.", "conferir gênero da qualificação"),
            base("domiciliado", "ERRO_GENERO", "CONFERIR", "Conferir se a qualificação corresponde a pessoa masculina.", "conferir gênero da qualificação"),
        ]
