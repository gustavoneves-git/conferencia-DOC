from pathlib import Path

from flask import current_app


class PromptLoader:
    def load(self, name: str, variables: dict | None = None) -> str:
        path = current_app.config["BASE_DIR"] / "app" / "ai" / "prompts" / name
        if not Path(path).exists():
            path = Path(__file__).parent / "prompts" / name
        prompt = Path(path).read_text(encoding="utf-8")
        for key, value in (variables or {}).items():
            prompt = prompt.replace("{{" + key + "}}", str(value))
        return prompt
