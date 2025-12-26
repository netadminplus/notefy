def test_export_workflow(self, client):
        """Test export functionality"""
        # Create one simple note
        client.post("/api/notes", json={"title": "Export", "content": "test"})

        # Export JSON - use follow_redirects just in case
        json_res = client.get("/api/export/json", follow_redirects=True)
        assert json_res.status_code == 200
        
        # Export Markdown
        md_res = client.get("/api/export/markdown", follow_redirects=True)
        assert md_res.status_code == 200