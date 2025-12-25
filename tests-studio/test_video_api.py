import pytest
from fastapi.testclient import TestClient
from studio.app import app
import database
import os

# Use a test database
TEST_DB_PATH = "data/test_story_studio_video_api.db"

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

def test_generate_video_endpoint():
    """Test the POST /api/generate_video endpoint."""
    payload = {
        "story_name": "test_story",
        "files": ["file1.png", "file2.png"],
        "transition": "none",
        "duration": 2.0
    }
    
    response = client.post("/api/generate_video", json=payload)
    
    # It should fail initially because it's not implemented (404)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "submitted"
    assert "video_id" in data
    
    # Verify record in DB
    videos = database.get_all_videos() # This only gets 'completed'
    # Check directly in DB for pending
    conn = database.get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM generated_videos WHERE id = ?", (data["video_id"],))
    row = c.fetchone()
    conn.close()
    
    assert row is not None
    assert row["story_name"] == "test_story"
    assert row["status"] == "pending"
