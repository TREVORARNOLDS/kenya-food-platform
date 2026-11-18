import pytest

from app import create_app


@pytest.fixture(scope="session")
def app():
    return create_app("testing")


@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def db_session(app):
    """Creates tables in the TEST database only, and drops them afterwards."""
    from app.extensions import db

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()
