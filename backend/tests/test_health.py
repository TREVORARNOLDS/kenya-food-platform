from unittest.mock import patch


def test_app_factory_uses_testing_config(app):
    assert app.config["TESTING"] is True


def test_health_ok_with_real_database(client):
    resp = client.get("/api/v1/health/")
    assert resp.status_code == 200
    assert resp.json["database"]["connected"] is True


def test_health_reports_degraded_when_db_fails(client):
    with patch("app.api.health.routes.db.session.execute", side_effect=Exception("down")):
        resp = client.get("/api/v1/health/")
    assert resp.status_code == 503
    assert resp.json["status"] == "degraded"