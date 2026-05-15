import json
from datetime import datetime

from flask import current_app

from app.ai.json_guard import extract_json, validate_review_payload


class AIClient:
    def __init__(self):
        self.mode = current_app.config["AI_MODE"]
        self.model = current_app.config["OPENAI_MODEL"] or "gpt-4.1-mini"

    def review_document(self, prompt: str, mock_issues: list[dict] | None = None) -> dict:
        if self.mode == "mock":
            payload = self._mock_review(mock_issues or [])
            return validate_review_payload(payload)
        try:
            raw = self._call_openai(prompt)
            self._save_raw(raw)
            return validate_review_payload(extract_json(raw))
        except Exception as exc:
            payload = self._fallback_error_payload(str(exc))
            return validate_review_payload(payload)

    def generate_json(self, prompt: str, fallback: dict) -> dict:
        if self.mode == "mock":
            return fallback
        try:
            raw = self._call_openai(prompt)
            self._save_raw(raw)
            return extract_json(raw)
        except Exception:
            return fallback

    def _call_openai(self, prompt: str) -> str:
        api_key = current_app.config["OPENAI_API_KEY"]
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY ausente.")
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Responda exclusivamente com JSON valido."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
        )
        return response.choices[0].message.content or "{}"

    def _save_raw(self, raw: str) -> None:
        if not current_app.config["SAVE_AI_RAW"] or current_app.config["FLASK_ENV"] != "development":
            return
        folder = current_app.config["BASE_DIR"] / "storage" / "ai_raw"
        folder.mkdir(parents=True, exist_ok=True)
        name = datetime.now().strftime("%Y%m%d_%H%M%S_%f.json")
        (folder / name).write_text(raw, encoding="utf-8")

    def _mock_review(self, issues: list[dict]) -> dict:
        apontamentos = []
        for idx, issue in enumerate(issues, start=1):
            apontamentos.append(
                {
                    "codigo": f"E{idx:03d}",
                    "pagina_estimada": issue.get("page_number"),
                    "trecho_original": issue.get("original_text", ""),
                    "tipo": issue.get("issue_type", "OUTRO"),
                    "gravidade": issue.get("severity", "MEDIA"),
                    "explicacao": issue.get("explanation", ""),
                    "sugestao": issue.get("suggestion", ""),
                    "justificativa_tecnica": issue.get("technical_reason", ""),
                    "acao_recomendada": issue.get("recommended_action", "Aplicar a correcao sugerida apos revisao humana."),
                    "pode_ser_grifado": issue.get("can_be_highlighted", True),
                    "source": issue.get("source", "RULE"),
                }
            )
        return {
            "documento": {"tipo_documental_estimado": "", "empresa_identificada": "", "data_documento": "", "nivel_confianca_tipo": "mock"},
            "resumo": {"total_apontamentos": len(apontamentos)},
            "apontamentos": apontamentos,
            "versao_corrigida_sugerida": {"observacao": "Mock local.", "texto_corrigido_integral": ""},
            "alertas_humanos": [],
        }

    def _fallback_error_payload(self, message: str) -> dict:
        return {
            "documento": {},
            "resumo": {},
            "apontamentos": [
                {
                    "codigo": "E001",
                    "pagina_estimada": None,
                    "trecho_original": "",
                    "tipo": "DADO_A_CONFERIR",
                    "gravidade": "CONFERIR",
                    "explicacao": "A analise por IA nao foi concluida.",
                    "sugestao": "Executar novamente apos verificar configuracao da API.",
                    "justificativa_tecnica": message[:300],
                    "acao_recomendada": "Revisar manualmente e conferir configuracao da IA.",
                    "pode_ser_grifado": False,
                }
            ],
        }
