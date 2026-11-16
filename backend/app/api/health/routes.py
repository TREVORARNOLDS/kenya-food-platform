from flask import current_app
from flask.views import MethodView
from flask_smorest import Blueprint
from sqlalchemy import text

from app.extensions import db

blp = Blueprint("health", __name__, url_prefix="/api/v1/health", description="Service health")


@blp.route("/")
class HealthCheck(MethodView):
    def get(self):
        database = {"connected": False}
        try:
            db.session.execute(text("SELECT 1"))
            database["postgis_version"] = db.session.execute(
                text("SELECT PostGIS_Version()")
            ).scalar()
            database["connected"] = True
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Database health check failed")

        healthy = database["connected"]
        return {
            "status": "ok" if healthy else "degraded",
            "service": "kenya-food-platform-api",
            "database": database,
        }, (200 if healthy else 503)