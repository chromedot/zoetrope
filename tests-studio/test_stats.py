import pytest
from fastapi.testclient import TestClient
from studio.app import app
import database
import os

# Use a test database
TEST_DB_PATH = "data/test_story_studio.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    # Monkeypatch the DB_PATH in database module
    monkeypatch.setattr(database, "DB_PATH", TEST_DB_PATH)
    
    # Initialize the test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    database.init_db()
    
    yield
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

client = TestClient(app)

def test_get_stats_empty():
    """Test get_stats when no images have been generated."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 0
    assert data["avg_time"] == 0
    assert data["total_time"] == 0

def test_get_stats_with_data():
    """Test get_stats with some completed generations."""
    # Manually insert some data into the test DB
    conn = database.get_db_connection()
    c = conn.cursor()
    # Insert two completed generations
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status, generation_duration) VALUES (?, ?, ?, ?)",
        (0, "test_story", "completed", 10.5)
    )
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status, generation_duration) VALUES (?, ?, ?, ?)",
        (1, "test_story", "completed", 20.5)
    )
    # Insert one pending generation (should not be counted)
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (2, "test_story", "pending")
    )
    conn.commit()
    conn.close()
    
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["avg_time"] == 15.5
    assert data["total_time"] == 31.0

def test_get_dashboard_stats():
    """Test get_dashboard_stats for a summary of all stories."""
    # Insert data for two different stories
    conn = database.get_db_connection()
    c = conn.cursor()
    # Story 1: 3 total, 2 completed, 1 pending
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (0, "story_1", "completed")
    )
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (1, "story_1", "completed")
    )
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (2, "story_1", "pending")
    )
    # Story 2: 1 total, 1 completed
    c.execute(
        "INSERT INTO generated_images (scene_index, story_name, status) VALUES (?, ?, ?)",
        (0, "story_2", "completed")
    )
    conn.commit()
    conn.close()
    
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    s1 = next(s for s in data if s["story_name"] == "story_1")
    assert s1["total_scenes"] == 3
    assert s1["completed_scenes"] == 2
    assert s1["status"] == "in_progress"
    
    s2 = next(s for s in data if s["story_name"] == "story_2")
    assert s2["total_scenes"] == 1
    assert s2["completed_scenes"] == 1
    assert s2["status"] == "completed"
