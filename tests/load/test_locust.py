"""
Load testing with Locust
Run with: locust -f tests/load/test_locust.py --host=https://notefy.ramtiin.ir
"""

from locust import HttpUser, task, between
import random
import json


class NoteUser(HttpUser):
    """Simulates a user interacting with Notefy"""

    wait_time = between(1, 3)

    def on_start(self):
        """Setup - runs when user starts"""
        self.note_ids = []
        self.tags = ["work", "personal", "ideas", "todo", "important", "urgent"]

    @task(10)
    def view_homepage(self):
        """View the main page"""
        self.client.get("/")

    @task(8)
    def get_all_notes(self):
        """Get all notes"""
        with self.client.get("/api/notes", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        # Store note IDs for later use
                        self.note_ids = [note["id"] for note in data.get("notes", [])]
                        response.success()
                    else:
                        response.failure("API returned success=False")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(5)
    def create_note(self):
        """Create a new note"""
        note_data = {
            "title": f"Load Test Note {random.randint(1000, 9999)}",
            "content": f"This is a test note created by load testing. Random number: {random.random()}",
            "tags": random.sample(self.tags, k=random.randint(1, 3)),
            "is_pinned": random.choice([True, False]),
            "color": random.choice(["default", "red", "blue", "green", "yellow"]),
        }

        with self.client.post("/api/notes", json=note_data, catch_response=True) as response:
            if response.status_code == 201:
                try:
                    data = response.json()
                    if data.get("success") and "note" in data:
                        self.note_ids.append(data["note"]["id"])
                        response.success()
                    else:
                        response.failure("Note creation failed")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(3)
    def get_specific_note(self):
        """Get a specific note"""
        if self.note_ids:
            note_id = random.choice(self.note_ids)
            with self.client.get(f"/api/notes/{note_id}", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    # Note might have been deleted
                    self.note_ids.remove(note_id)
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(3)
    def update_note(self):
        """Update an existing note"""
        if self.note_ids:
            note_id = random.choice(self.note_ids)
            update_data = {
                "title": f"Updated Note {random.randint(1000, 9999)}",
                "content": f"Updated content at {random.random()}",
                "is_pinned": random.choice([True, False]),
            }

            with self.client.put(f"/api/notes/{note_id}", json=update_data, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    self.note_ids.remove(note_id)
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(4)
    def search_notes(self):
        """Search for notes"""
        search_terms = ["test", "note", "important", "work", "idea", "todo"]
        query = random.choice(search_terms)

        with self.client.get(f"/api/search?q={query}", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        response.success()
                    else:
                        response.failure("Search returned success=False")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(2)
    def health_check(self):
        """Check application health"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "UP":
                        response.success()
                    else:
                        response.failure("Health check status not UP")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")

    @task(1)
    def delete_note(self):
        """Delete a note"""
        if len(self.note_ids) > 10:  # Only delete if we have enough notes
            note_id = random.choice(self.note_ids)
            with self.client.delete(f"/api/notes/{note_id}", catch_response=True) as response:
                if response.status_code == 200:
                    self.note_ids.remove(note_id)
                    response.success()
                elif response.status_code == 404:
                    self.note_ids.remove(note_id)
                    response.success()
                else:
                    response.failure(f"Got status code {response.status_code}")

    @task(1)
    def get_stats(self):
        """Get application statistics"""
        with self.client.get("/api/stats", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        response.success()
                    else:
                        response.failure("Stats returned success=False")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")


class HighLoadUser(HttpUser):
    """Aggressive load testing user"""

    wait_time = between(0.5, 1)

    @task(20)
    def rapid_get_notes(self):
        """Rapidly fetch notes"""
        self.client.get("/api/notes")

    @task(10)
    def rapid_create(self):
        """Rapidly create notes"""
        self.client.post(
            "/api/notes", json={"title": f"High Load {random.randint(1, 10000)}", "content": "High load testing"}
        )

    @task(5)
    def rapid_search(self):
        """Rapidly search"""
        self.client.get(f"/api/search?q=load{random.randint(1, 100)}")
