import pytest
from fastapi.testclient import TestClient
from studio.app import app
from unittest.mock import patch, AsyncMock
import os

client = TestClient(app)

# Mocking the manager because app.py uses it to get scene data
# and sanitize filename BEFORE using story_name for folder.
# We need to make sure the manager mocking works.

@patch("studio.app.tts_generator.generate", new_callable=AsyncMock)
@patch("studio.app.manager")
def test_generate_audio_path_traversal(mock_manager, mock_generate):
    """Test that path traversal attempts in story_name are rejected for TTS.

    Same safe_join(OUTPUT_DIR, request.story_name) guard as generate_sfx:
    it raises ValueError on escape, the endpoint returns an error before
    any directory is created. Verified directly: os.makedirs is never
    called, and no narration audio is generated.
    """
    mock_manager.story_data = [{"scene": 1, "description": "test scene"}]
    mock_manager.sanitize_filename.return_value = "safe_desc"
    mock_manager.save_story.return_value = None

    payload = {
        "scene_index": 0,
        "text": "narration text",
        "story_name": "../../../secrets"
    }

    with patch("os.makedirs") as mock_makedirs:
        response = client.post("/api/generate_audio", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid story name" in data["message"]

        mock_makedirs.assert_not_called()
        mock_generate.assert_not_called()
