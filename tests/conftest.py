import pytest
from app import create_app, db
from sqlalchemy import text

@pytest.fixture(scope="session")
def app():
    _app = create_app("testing")
    with _app.app_context():
        db.create_all()
        yield _app
        db.drop_all()

@pytest.fixture(autouse=True)
def clean_database(app):
    with app.app_context():
        # Clear all data
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        # CRITICAL: Close the session to release DB locks
        db.session.remove()