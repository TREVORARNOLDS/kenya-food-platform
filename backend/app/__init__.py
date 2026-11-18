import logging
import os

from flask import Flask

from .config import config_by_name
from .extensions import cors, db, include_object, migrate, smorest_api


def create_app(config_name: str | None = None) -> Flask:
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Safety: tests must never touch the dev/production database
    if config_name == "testing":
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if not uri or uri == os.getenv("DATABASE_URL"):
            raise RuntimeError("TEST_DATABASE_URL must be set and differ from DATABASE_URL")

    logging.basicConfig(level=logging.INFO)

    db.init_app(app)
    migrate.init_app(app, db, include_object=include_object)
    smorest_api.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from . import models  # noqa: F401  (registers models with SQLAlchemy/Alembic)
    from .api.health.routes import blp as health_blp

    smorest_api.register_blueprint(health_blp)

    from .cli import ingest_cli

    app.cli.add_command(ingest_cli)
    return app