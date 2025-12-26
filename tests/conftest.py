import pytest
from app import create_app, db

@pytest.fixture(scope="session")
def app():
    """Create application for the test session"""
    _app = create_app("testing")
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Test CLI runner for the app"""
    return app.test_cli_runner()