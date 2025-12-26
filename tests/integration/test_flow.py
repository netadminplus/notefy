# tests/unit/test_app.py
import pytest
from app import create_app, db
from app.models import Note


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoint:
    def test_health_check_success(self, client):
        """Test health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"
        assert "database" in data


class TestNoteModel:
    def test_create_note(self, app):
        """Test creating a note"""
        with app.app_context():
            note = Note(title="Test Note", content="Test Content", tags="test,unit")
            db.session.add(note)
            db.session.commit()

            assert note.id is not None
            assert note.title == "Test Note"
            assert note.content == "Test Content"

    def test_note_to_dict(self, app):
        """Test note serialization"""
        with app.app_context():
            note = Note(title="Test", content="Content", tags="tag1,tag2")
            db.session.add(note)
            db.session.commit()

            note_dict = note.to_dict()
            assert note_dict["title"] == "Test"
            assert note_dict["content"] == "Content"
            assert note_dict["tags"] == ["tag1", "tag2"]

    def test_note_to_markdown(self, app):
        """Test markdown export"""
        with app.app_context():
            note = Note(title="Markdown Test", content="Test markdown content", tags="markdown,export")
            db.session.add(note)
            db.session.commit()

            markdown = note.to_markdown()
            assert "# Markdown Test" in markdown
            assert "Test markdown content" in markdown
            assert "#markdown" in markdown


class TestNoteAPI:
    def test_get_empty_notes(self, client):
        """Test getting notes when none exist"""
        response = client.get("/api/notes")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["notes"]) == 0

    def test_create_note_api(self, client):
        """Test creating note via API"""
        note_data = {"title": "API Test", "content": "Testing API", "tags": ["api", "test"]}
        response = client.post("/api/notes", json=note_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data["success"] is True
        assert data["note"]["title"] == "API Test"

    def test_create_note_missing_fields(self, client):
        """Test creating note without required fields"""
        response = client.post("/api/notes", json={})
        assert response.status_code == 400

    def test_get_note_by_id(self, client):
        """Test getting specific note"""
        # Create a note first
        note_data = {"title": "Get Test", "content": "Content"}
        create_response = client.post("/api/notes", json=note_data)
        note_id = create_response.get_json()["note"]["id"]

        # Get the note
        response = client.get(f"/api/notes/{note_id}")
        assert response.status_code == 200
        data = response.get_json()
        assert data["note"]["title"] == "Get Test"

    def test_update_note(self, client):
        """Test updating a note"""
        # Create note
        note_data = {"title": "Original", "content": "Content"}
        create_response = client.post("/api/notes", json=note_data)
        note_id = create_response.get_json()["note"]["id"]

        # Update note
        update_data = {"title": "Updated", "content": "New Content"}
        response = client.put(f"/api/notes/{note_id}", json=update_data)
        assert response.status_code == 200
        data = response.get_json()
        assert data["note"]["title"] == "Updated"

    def test_delete_note(self, client):
        """Test deleting a note"""
        # Create note
        note_data = {"title": "Delete Me", "content": "Content"}
        create_response = client.post("/api/notes", json=note_data)
        note_id = create_response.get_json()["note"]["id"]

        # Delete note
        response = client.delete(f"/api/notes/{note_id}")
        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 404


class TestSearchAPI:
    def test_search_notes(self, client):
        """Test searching notes"""
        # Create test notes
        client.post("/api/notes", json={"title": "Python Tutorial", "content": "Learn Python programming"})
        client.post("/api/notes", json={"title": "JavaScript Guide", "content": "Learn JavaScript"})

        # Search
        response = client.get("/api/search?q=Python")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["notes"]) >= 1


class TestExportAPI:
    def test_export_json(self, client):
        """Test JSON export"""
        client.post("/api/notes", json={"title": "Export Test", "content": "Test export"})

        response = client.get("/api/export/json")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_export_markdown(self, client):
        """Test Markdown export"""
        client.post("/api/notes", json={"title": "Export Test", "content": "Test export"})

        response = client.get("/api/export/markdown")
        assert response.status_code == 200
        assert "text/markdown" in response.content_type


# tests/integration/test_flow.py
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestFullUserFlow:
    def test_complete_note_lifecycle(self, client):
        """Test complete CRUD flow"""
        # Create
        create_response = client.post(
            "/api/notes",
            json={
                "title": "Integration Test",
                "content": "Full lifecycle test",
                "tags": ["integration", "test"],
                "is_pinned": True,
                "color": "blue",
            },
        )
        assert create_response.status_code == 201
        note_id = create_response.get_json()["note"]["id"]

        # Read
        get_response = client.get(f"/api/notes/{note_id}")
        assert get_response.status_code == 200
        note = get_response.get_json()["note"]
        assert note["title"] == "Integration Test"
        assert note["is_pinned"] is True
        assert note["color"] == "blue"

        # Update
        update_response = client.put(
            f"/api/notes/{note_id}", json={"title": "Updated Title", "content": "Updated content", "is_pinned": False}
        )
        assert update_response.status_code == 200
        updated_note = update_response.get_json()["note"]
        assert updated_note["title"] == "Updated Title"
        assert updated_note["is_pinned"] is False

        # Delete
        delete_response = client.delete(f"/api/notes/{note_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_get = client.get(f"/api/notes/{note_id}")
        assert final_get.status_code == 404

    def test_multi_note_operations(self, client):
        """Test operations with multiple notes"""
        # Create multiple notes
        notes = []
        for i in range(5):
            response = client.post(
                "/api/notes", json={"title": f"Note {i}", "content": f"Content {i}", "tags": [f"tag{i}"]}
            )
            notes.append(response.get_json()["note"]["id"])

        # Get all notes
        list_response = client.get("/api/notes")
        assert len(list_response.get_json()["notes"]) == 5

        # Search
        search_response = client.get("/api/search?q=Note 3")
        assert len(search_response.get_json()["notes"]) >= 1

        # Delete one
        client.delete(f"/api/notes/{notes[0]}")
        list_response = client.get("/api/notes")
        assert len(list_response.get_json()["notes"]) == 4

    def test_export_workflow(self, client):
        """Test export functionality"""
        # Create notes
        for i in range(3):
            client.post("/api/notes", json={"title": f"Export Note {i}", "content": f"Export content {i}"})

        # Export JSON
        json_response = client.get("/api/export/json")
        assert json_response.status_code == 200

        # Export Markdown
        md_response = client.get("/api/export/markdown")
        assert md_response.status_code == 200


# tests/conftest.py
import pytest


@pytest.fixture(scope="session")
def app():
    """Create application for the test session"""
    from app import create_app

    app = create_app("testing")
    return app
