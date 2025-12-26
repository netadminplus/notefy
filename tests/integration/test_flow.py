import pytest

# Note: fixtures 'app' and 'client' are automatically
# loaded from tests/conftest.py


def test_export_workflow(client):
    """Test export functionality without the class-based 'self' argument"""
    # Create one simple note to ensure there is data to export
    client.post("/api/notes", json={"title": "Export Test", "content": "test data"})

    # Test JSON Export
    json_res = client.get("/api/export/json")
    assert json_res.status_code == 200
    assert json_res.content_type == "application/json"

    # Test Markdown Export
    md_res = client.get("/api/export/markdown")
    assert md_res.status_code == 200
    assert "text/markdown" in md_res.content_type
    # Verify content
    assert b"Export Test" in md_res.data
