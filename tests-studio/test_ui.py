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
