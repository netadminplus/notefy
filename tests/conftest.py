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

@pytest.fixture(autouse=True)
def clean_database(app):
    """Ensure a clean database for every single test"""
    with app.app_context():
        # Clear all data from tables without dropping them
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()