from app import create_app
from app.ai.client import AIClient


def test_ai_client_mock_returns_empty_ai_payload():
    app = create_app()
    app.config["AI_MODE"] = "mock"
    with app.app_context():
        payload = AIClient().review_document("prompt", mock_issues=[{"original_text": "x"}])
    assert payload["normalized_issues"] == []
    assert payload["normalized_summary"]["total"] == 0


def test_ai_client_api_without_key_falls_back():
    app = create_app()
    app.config["AI_MODE"] = "api"
    app.config["OPENAI_API_KEY"] = ""
    with app.app_context():
        payload = AIClient().review_document("prompt")
    assert payload["fallback_used"] is True
    assert payload["normalized_issues"] == []
    assert "OPENAI_API_KEY" in payload["ai_error"]


def test_ai_client_api_error_falls_back(monkeypatch):
    app = create_app()
    app.config["AI_MODE"] = "api"
    app.config["OPENAI_API_KEY"] = "test-key"

    def fail_call(_self, _prompt):
        raise TimeoutError("timed out")

    monkeypatch.setattr(AIClient, "_call_openai", fail_call)
    with app.app_context():
        payload = AIClient().review_document("prompt")
    assert payload["fallback_used"] is True
    assert "Tempo limite" in payload["ai_error"]
