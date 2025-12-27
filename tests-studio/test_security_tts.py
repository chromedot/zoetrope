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
    """Test that path traversal attempts in story_name are sanitized or rejected for TTS."""
    
    # Mock manager behavior
    mock_manager.story_data = [{"scene": 1, "description": "test scene"}]
    mock_manager.sanitize_filename.return_value = "safe_desc"
    mock_manager.save_story.return_value = None

    # Payload with traversal in story_name
    payload = {
        "scene_index": 0,
        "text": "narration text",
        "story_name": "../../../secrets" 
    }
    
    # We mock os.makedirs to verify the path it receives.
    with patch("os.makedirs") as mock_makedirs:
        response = client.post("/api/generate_audio", json=payload)
        
        # Currently, this should succeed (status 200) but Create the bad directory.
        # We assert that it does NOT create the bad directory.
        
        # For the FAILING test, we expect this assertion to fail because the code is not fixed yet.
        
        assert response.status_code == 200 
        
        args, _ = mock_makedirs.call_args
        created_dir = args[0]
        
        # Expect sanitization
        assert ".." not in created_dir
        # Should be sanitized to just "secrets"
        assert created_dir.endswith("/secrets/audio")
