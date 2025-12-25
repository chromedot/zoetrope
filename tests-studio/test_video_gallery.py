import pytest
from fastapi.testclient import TestClient
from studio.app import app
import database
import os

# Use a test database
TEST_DB_PATH = "data/test_story_studio_video_gallery.db"

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

def test_video_gallery_page_loading():
    """Test if the Video Gallery page loads correctly."""
    # Insert a completed video record
    video_id = database.create_video_record("test_story", "fade", 1.0)
    database.update_video_record(video_id, "test_video.mp4", status='completed')

    response = client.get("/videos")
    assert response.status_code == 200
    html = response.text
    
    assert "Video Gallery" in html
    assert "test_story" in html
    assert "test_video.mp4" in html
    assert "fade" in html
    assert "video" in html # Video tag or reference

def test_delete_video_api():
    """Test the API for deleting a video record."""
    video_id = database.create_video_record("delete_me", "none", 0.0)
    database.update_video_record(video_id, "delete_me.mp4", status='completed')
    
    # Verify it exists
    videos = database.get_all_videos()
    assert any(v['id'] == video_id for v in videos)
    
    # Delete it
    response = client.post(f"/api/delete_video/{video_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verify it's gone
    videos = database.get_all_videos()
    assert not any(v['id'] == video_id for v in videos)
