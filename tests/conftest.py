import pytest
from app import create_app, db
from sqlalchemy import text


@pytest.fixture(scope="session")
def app():
    """Create application for the test session"""
    _app = create_app("testing")
    with _app.app_context():
        db.create_all()
        yield _app
        # Force close all connections before dropping
        db.session.remove()
        db.engine.dispose()
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_database(app):
    """Clean database between every single test"""
    with app.app_context():
        db.session.expire_all()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.remove()  # Release the lock!
