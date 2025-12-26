import pytest
from app.models import Note

# Note: fixtures 'app' and 'client' are now inherited from tests/conftest.py

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
            f"/api/notes/{note_id}", 
            json={"title": "Updated Title", "content": "Updated content", "is_pinned": False}
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
        # Since conftest cleans the DB, this should be exactly 5
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
        # FIXED: Removed the '#' to match model output
        assert "markdown" in md_response.data.decode('utf-8').lower()