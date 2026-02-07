from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Flask

from app.datastore import build_data_store
from app.routes import bp


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)

    default_db_path = Path(__file__).resolve().parents[1] / "results.sqlite"
    app.config.from_mapping(
        SITE_TITLE="reproducibilityindex.ai",
        DB_BACKEND="sqlite",
        SQLITE_DB_PATH=str(default_db_path),
    )

    if test_config:
        app.config.update(test_config)

    app.extensions["data_store"] = build_data_store(app.config)

    @app.context_processor
    def inject_globals() -> dict[str, object]:
        return {
            "site_title": app.config["SITE_TITLE"],
            "conference_nav": app.extensions["data_store"].list_conferences(),
        }

    app.register_blueprint(bp)
    return app
