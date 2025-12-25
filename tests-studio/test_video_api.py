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
    # Create dummy files
    for f in ["file1.png", "file2.png"]:
        with open(f, "w") as fd:
            fd.write("dummy")
            
    payload = {
        "story_name": "test_story",
        "files": ["file1.png", "file2.png"],
        "transition": "none",
        "duration": 2.0
    }
    
    try:
        response = client.post("/api/generate_video", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "submitted"
        assert "video_id" in data
        
        # Verify record in DB
        conn = database.get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM generated_videos WHERE id = ?", (data["video_id"],))
        row = c.fetchone()
        conn.close()
        
        assert row is not None
        assert row["story_name"] == "test_story"
        # Since BackgroundTasks run immediately in TestClient, it might already be 'completed' or 'failed'
        # but it should at least exist and have been initiated.
        assert row["status"] in ["pending", "completed", "failed"]
    finally:
        # Cleanup
        for f in ["file1.png", "file2.png"]:
            if os.path.exists(f):
                os.remove(f)
