import pytest
from fastapi.testclient import TestClient
from studio.app import app
import database
import os
from unittest.mock import patch, AsyncMock

# Use a test database
TEST_DB_PATH = "data/test_story_studio_audio_api.db"

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

def test_generate_audio_endpoint_success():
    """Test successful POST /api/generate_audio."""
    payload = {
        "scene_index": 0,
        "text": "Test narration text",
        "story_name": "geronimo"
    }
    
    with patch("scripts.audio_utils.EdgeTTSGenerator.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "geronimo/audio/scene_00_test.mp3"
        
        response = client.post("/api/generate_audio", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "audio_url" in data
        assert "/images/geronimo/audio/" in data["audio_url"]
        assert data["audio_url"].endswith(".mp3")
        
        # Verify DB update (logic needs to be in app.py or database.py)
        # We expect it to update the latest record or specific record for that scene
        # For simplicity, we'll check if any record for that scene has the audio_file set
        # But wait, the API might just return the URL and let the frontend handle UI updates.
        # However, it SHOULD persist to the story file via StoryManager.
