import pytest
from fastapi.testclient import TestClient
from studio.app import app
import database
import os

# Use a test database
TEST_DB_PATH = "data/test_story_studio_ui.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", TEST_DB_PATH)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    database.init_db()
    yield
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

client = TestClient(app)

def test_dashboard_page_loading():
    """Test if the dashboard page loads correctly and contains expected elements."""
    # Insert some mock data
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (0, "test_story_ui", "completed")
    )
    conn.commit()
    conn.close()

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.text
    
    # Check for basic UI components
    assert "Story Dashboard" in html
    assert "test_story_ui" in html
    assert "table" in html # Should have a table of stories
    assert "Review" in html # Action button
    assert "Delete" in html # Action button

def test_delete_story_api():
    """Test the API endpoint for deleting a story."""
    # Insert data for a story to delete
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (0, "to_delete", "completed")
    )
    conn.commit()
    conn.close()

    # Verify story exists
    stats = database.get_dashboard_stats()
    assert any(s["story_name"] == "to_delete" for s in stats)

    # Call delete endpoint (to be implemented)
    response = client.post("/api/delete_story/to_delete")
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify story is gone
    stats = database.get_dashboard_stats()
    assert not any(s["story_name"] == "to_delete" for s in stats)
