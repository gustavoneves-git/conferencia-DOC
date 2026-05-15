import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.database.db import init_db


def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    load_dotenv(base_dir / ".env")

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret"),
        DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///data/conferencia_documento.db"),
        AI_MODE=os.getenv("AI_MODE", "mock").lower(),
        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
        OPENAI_MODEL=os.getenv("OPENAI_MODEL", ""),
        DEFAULT_OPENAI_MODEL=os.getenv("DEFAULT_OPENAI_MODEL", "gpt-4.1-mini"),
        OPENAI_TIMEOUT=float(os.getenv("OPENAI_TIMEOUT", "45")),
        SAVE_AI_RAW=os.getenv("SAVE_AI_RAW", "false").lower() == "true",
        FLASK_ENV=os.getenv("FLASK_ENV", "production"),
        BASE_DIR=base_dir,
        MAX_CONTENT_LENGTH=25 * 1024 * 1024,
        DEBUG=os.getenv("FLASK_ENV") == "development",
    )

    for folder in [
        "data",
        "storage/uploads",
        "storage/extracted",
        "storage/annotated",
        "storage/reports",
        "storage/corrected",
        "storage/final",
        "storage/ai_raw",
        "storage/tmp",
    ]:
        (base_dir / folder).mkdir(parents=True, exist_ok=True)

    init_db(app)

    from app.routes.dashboard_routes import bp as dashboard_bp
    from app.routes.document_routes import bp as document_bp
    from app.routes.review_routes import bp as review_bp
    from app.routes.generation_routes import bp as generation_bp
    from app.routes.export_routes import bp as export_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(document_bp)
    app.register_blueprint(review_bp)
    app.register_blueprint(generation_bp)
    app.register_blueprint(export_bp)
    return app
