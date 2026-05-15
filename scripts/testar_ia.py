import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app
from app.ai.client import AIClient


def main() -> int:
    app = create_app()
    with app.app_context():
        client = AIClient()
        if client.mode != "api":
            print(f"AI_MODE atual: {client.mode}. Para testar a API, configure AI_MODE=api no .env.")
            print(f"Modelo configurado/padrão: {client.model}")
            return 0
        if not app.config["OPENAI_API_KEY"]:
            print("OPENAI_API_KEY ausente. Configure a chave no .env para testar a API.")
            print(f"Modelo configurado/padrão: {client.model}")
            return 0
        result = client.test_connection()
        print(result["message"])
        print(f"Modo: {result['mode']}")
        print(f"Modelo usado: {result['model']}")
        return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
