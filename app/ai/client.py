import json
from datetime import datetime

from flask import current_app

from app.ai.json_guard import extract_json, validate_review_payload


class AIClient:
    def __init__(self):
        self.mode = (current_app.config["AI_MODE"] or "mock").lower()
        self.model = current_app.config["OPENAI_MODEL"] or current_app.config["DEFAULT_OPENAI_MODEL"]
        self.timeout = current_app.config.get("OPENAI_TIMEOUT", 45)

    def review_document(self, prompt: str, mock_issues: list[dict] | None = None) -> dict:
        if self.mode == "mock":
            payload = self._mock_review(mock_issues or [])
            return validate_review_payload(payload)
        try:
            raw = self._call_openai(prompt)
            if not raw.strip():
                raise RuntimeError("A API retornou resposta vazia.")
            self._save_raw(raw)
            payload = validate_review_payload(extract_json(raw))
            payload["fallback_used"] = False
            payload["ai_error"] = ""
            return payload
        except Exception as exc:
            payload = self._fallback_error_payload(self._friendly_error(exc))
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

    def test_connection(self) -> dict:
        if self.mode != "api":
            return {"ok": False, "mode": self.mode, "model": self.model, "message": "AI_MODE não está em api."}
        try:
            raw = self._call_openai(
                'Responda exclusivamente em JSON válido: {"status":"ok","mensagem":"conectado"}'
            )
            payload = extract_json(raw)
            ok = payload.get("status") == "ok"
            return {
                "ok": ok,
                "mode": self.mode,
                "model": self.model,
                "message": "IA conectada com sucesso." if ok else "A IA respondeu, mas o JSON não veio no formato esperado.",
                "payload": payload,
            }
        except Exception as exc:
            return {"ok": False, "mode": self.mode, "model": self.model, "message": self._friendly_error(exc)}

    def _call_openai(self, prompt: str) -> str:
        api_key = current_app.config["OPENAI_API_KEY"]
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY ausente.")
        from openai import OpenAI

        client = OpenAI(api_key=api_key, timeout=self.timeout)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Responda exclusivamente com JSON válido. Não use markdown."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
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
        return {
            "documento": {"tipo_documental_estimado": "", "empresa_identificada": "", "data_documento": "", "nivel_confianca_tipo": "mock"},
            "resumo": {"total_apontamentos": 0},
            "apontamentos": [],
            "versao_corrigida_sugerida": {"observacao": "Mock local.", "texto_corrigido_integral": ""},
            "alertas_humanos": [],
        }

    def _fallback_error_payload(self, message: str) -> dict:
        return {
            "documento": {},
            "resumo": {},
            "apontamentos": [],
            "fallback_used": True,
            "ai_error": message,
            "ai_error_message": "A análise por IA não foi concluída. O sistema continuou somente com regras fixas.",
            "versao_corrigida_sugerida": {"observacao": "", "texto_corrigido_integral": ""},
            "alertas_humanos": [{"codigo": "AIA001", "descricao": "Falha na IA", "motivo": message}],
        }

    def _friendly_error(self, exc: Exception) -> str:
        name = exc.__class__.__name__.lower()
        message = str(exc)[:300]
        if "auth" in name or "401" in message or "api key" in message.lower():
            return "Falha de autenticação na API. Verifique OPENAI_API_KEY no .env."
        if "timeout" in name or "timed out" in message.lower():
            return "Tempo limite excedido ao chamar a API de IA. Tente novamente ou aumente OPENAI_TIMEOUT."
        if "model" in message.lower() or "404" in message:
            return "Modelo de IA inválido ou indisponível. Verifique OPENAI_MODEL no .env."
        if "json" in message.lower():
            return "A IA respondeu em formato JSON inválido. A revisão continuará com regras fixas."
        if "OPENAI_API_KEY" in message:
            return "OPENAI_API_KEY ausente. Configure a chave no .env para usar AI_MODE=api."
        return f"Falha ao chamar a API de IA: {message}"
