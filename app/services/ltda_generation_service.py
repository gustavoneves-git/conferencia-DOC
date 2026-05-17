import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from flask import current_app

from app.ai.client import AIClient
from app.ai.prompt_loader import PromptLoader
from app.generation.generation_payload_builder import build_ltda_constituicao_payload
from app.services.advanced_case_detector_service import detect_advanced_case
from app.services.docx_output_service import DocxOutputService
from app.services.file_naming_service import clean_document_name
from app.services.ltda_generation_validation_service import LtdaGenerationValidationService


class LtdaGenerationService:
    def generate_constituicao(self, form_data: dict) -> dict:
        payload = build_ltda_constituicao_payload(form_data)
        validation = LtdaGenerationValidationService().validate(payload)
        advanced = detect_advanced_case(payload)
        if advanced["is_advanced"]:
            return {
                "status": "advanced_blocked",
                "payload": payload,
                "validation": validation,
                "advanced": advanced,
                "files": {},
                "alertas": [],
            }
        if not validation["valid"]:
            return {
                "status": "validation_error",
                "payload": payload,
                "validation": validation,
                "advanced": advanced,
                "files": {},
                "alertas": [],
            }

        fallback = self._mock_payload(payload)
        prompt = PromptLoader().load(
            "generate_constituicao_ltda.md",
            {"STRUCTURED_DATA": json.dumps(payload, ensure_ascii=False, indent=2)},
        )
        ai_payload = AIClient().generate_json(prompt, fallback)
        if ai_payload.get("status") != "ok":
            return {
                "status": "generation_error",
                "payload": payload,
                "validation": validation,
                "advanced": advanced,
                "files": {},
                "errors": ai_payload.get("errors", [{"field": "ai", "message": "A minuta não pôde ser gerada."}]),
                "alertas": ai_payload.get("alertas", []),
            }

        title = ai_payload.get("titulo") or "Contrato Social de Constituição de Sociedade Limitada"
        text = self._normalize_generated_minute_text(
            ai_payload.get("texto_minuta") or fallback["texto_minuta"],
            title,
            payload["empresa"]["razao_social"],
        )
        files = self._write_outputs(payload, title, text)
        return {
            "status": "ok",
            "payload": payload,
            "validation": validation,
            "advanced": advanced,
            "files": files,
            "titulo": title,
            "empresa": ai_payload.get("empresa") or payload["empresa"]["razao_social"],
            "alertas": ai_payload.get("alertas", []),
        }

    def _write_outputs(self, payload: dict, title: str, text: str) -> dict:
        base = current_app.config["BASE_DIR"] / "storage" / "generated"
        base.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company = clean_document_name(payload["empresa"]["razao_social"], "empresa")
        prefix = f"{company}__minuta_constituicao_ltda__{stamp}"
        payload_name = f"{company}__payload_geracao__{stamp}.json"
        docx = base / f"{prefix}.docx"
        pdf = base / f"{prefix}.pdf"
        payload_path = base / payload_name
        writer = DocxOutputService()
        writer.create_docx(str(docx), title, text, payload["empresa"]["razao_social"])
        writer.create_pdf(str(pdf), title, text, payload["empresa"]["razao_social"])
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"docx": str(docx), "pdf": str(pdf), "payload": str(payload_path)}

    def _mock_payload(self, payload: dict) -> dict:
        company = payload["empresa"]["razao_social"]
        return {
            "status": "ok",
            "document_type": payload["document_type"],
            "empresa": company,
            "titulo": "Contrato Social de Constituição de Sociedade Limitada",
            "texto_minuta": self._mock_text(payload),
            "alertas": [{"codigo": "REVISAO_HUMANA", "descricao": "Minuta gerada para revisão humana.", "motivo": "Validação operacional obrigatória antes de uso."}],
        }

    def _mock_text(self, payload: dict) -> str:
        empresa = payload["empresa"]
        capital = payload["capital"]
        socios = payload["socios"]
        admin = payload["administracao"]["administrador_nome"]
        sede = empresa["endereco_sede"]
        socios_text = "\n".join(self._qualify_socio(socio) for socio in socios)
        quotas_text = "\n".join(f"{s['nome_completo']} - {s['quotas']} quotas - {s['percentual']}%" for s in socios)
        integralizacao = "neste ato" if capital["forma_integralizacao"] == "ato" else f"em prazo futuro de {capital['prazo_integralizacao']}"
        testemunhas = payload["assinaturas"]["testemunhas"]
        advogado = payload["assinaturas"]["advogado"]
        signature_parts = [s["nome_completo"] for s in socios]
        if advogado.get("nome"):
            signature_parts.append(f"{advogado['nome']}\nOAB/{advogado.get('uf_oab', '')} {advogado.get('oab', '')}".strip())
        for testemunha in testemunhas:
            if testemunha.get("nome"):
                signature_parts.append(f"{testemunha['nome']}\n{testemunha.get('documento', '')}".strip())
        signatures = "\n\n".join(f"________________________________________\n{name}" for name in signature_parts)
        return f"""CONTRATO SOCIAL DE CONSTITUIÇÃO DE SOCIEDADE LIMITADA
{empresa['razao_social']}

Pelo presente instrumento particular, os abaixo assinados:

{socios_text}

Resolvem constituir uma sociedade empresária limitada, que se regerá pelas cláusulas seguintes:

CLÁUSULA PRIMEIRA - DA DENOMINAÇÃO
A sociedade adotará o nome empresarial {empresa['razao_social']}.

CLÁUSULA SEGUNDA - DA SEDE
A sociedade terá sede na {sede['logradouro']}, nº {sede['numero']}, {sede.get('complemento') or ''}, {sede['bairro']}, CEP {sede['cep']}, {sede['cidade']}/{sede['uf']}.

CLÁUSULA TERCEIRA - DO OBJETO SOCIAL
A sociedade terá por objeto social: {empresa['objeto_social']}.

CLÁUSULA QUARTA - DO CAPITAL SOCIAL
O capital social será de R$ {capital['capital_social']:.2f}, dividido em {capital['quotas_totais']} quotas, no valor unitário de R$ {capital['valor_unitario_quota']:.2f}, distribuídas entre os sócios da seguinte forma:
{quotas_text}

CLÁUSULA QUINTA - DA INTEGRALIZAÇÃO
O capital social será integralizado em moeda corrente nacional, {integralizacao}.

CLÁUSULA SEXTA - DA RESPONSABILIDADE DOS SÓCIOS
A responsabilidade de cada sócio é restrita ao valor de suas quotas, respondendo todos solidariamente pela integralização do capital social.

CLÁUSULA SÉTIMA - DA ADMINISTRAÇÃO
A administração da sociedade caberá a {admin}, que administrará a sociedade isoladamente, com poderes padrão de administração.

CLÁUSULA OITAVA - DO PRÓ-LABORE
O administrador poderá receber pró-labore, conforme deliberação dos sócios.

CLÁUSULA NONA - DAS DELIBERAÇÕES
As deliberações sociais serão tomadas na forma da legislação aplicável.

CLÁUSULA DÉCIMA - DO DESIMPEDIMENTO
O administrador declara, sob as penas da lei, não estar impedido de exercer a administração da sociedade.

CLÁUSULA DÉCIMA PRIMEIRA - DO EXERCÍCIO SOCIAL
O exercício social encerrará em 31 de dezembro de cada ano.

CLÁUSULA DÉCIMA SEGUNDA - DA CESSÃO DE QUOTAS
A cessão de quotas observará a legislação aplicável e o direito de preferência dos sócios.

CLÁUSULA DÉCIMA TERCEIRA - DO FORO
Fica eleito o foro da Comarca de {empresa['foro']} para dirimir dúvidas oriundas deste instrumento.

E, por estarem assim justos e contratados, assinam o presente instrumento.

{empresa['cidade_assinatura']}/{empresa['uf_assinatura']}, {empresa['data_instrumento']}.

{signatures}
"""

    def _qualify_socio(self, socio: dict) -> str:
        return (
            f"{socio['nome_completo']}, {socio.get('nacionalidade')}, {socio.get('estado_civil')}, "
            f"{socio.get('profissao')}, portador(a) do RG nº {socio.get('rg')}, "
            f"inscrito(a) no CPF sob nº {socio.get('cpf')}, residente e domiciliado(a) em {socio.get('endereco')}."
        )

    def _clean_generated_text(self, text: str) -> str:
        blocked = ("inteligência artificial", "inteligencia artificial", "openai", "chatgpt")
        lines = []
        for line in (text or "").splitlines():
            if any(term in line.casefold() for term in blocked):
                continue
            lines.append(line.rstrip())
        return "\n".join(lines).strip()

    def _normalize_generated_minute_text(self, text: str, title: str, company: str) -> str:
        cleaned = self._clean_generated_text(text)
        lines = cleaned.splitlines()
        title_key = self._line_key(title)
        company_key = self._line_key(company)
        normalized_lines = []
        header_zone = True
        removed_header_line = False

        for raw in lines:
            stripped = raw.strip()
            if header_zone and not stripped:
                if removed_header_line:
                    continue
                normalized_lines.append(raw.rstrip())
                continue

            key = self._line_key(stripped)
            is_duplicate_title = bool(title_key and key == title_key)
            is_duplicate_company = bool(company_key and key == company_key)

            if header_zone and (is_duplicate_title or is_duplicate_company):
                removed_header_line = True
                continue

            header_zone = False
            normalized_lines.append(raw.rstrip())

        return self._clean_generated_text("\n".join(normalized_lines))

    def _line_key(self, value: str) -> str:
        without_accents = "".join(
            char for char in unicodedata.normalize("NFD", value or "")
            if unicodedata.category(char) != "Mn"
        )
        return re.sub(r"[^A-Z0-9]+", "", without_accents.upper())
