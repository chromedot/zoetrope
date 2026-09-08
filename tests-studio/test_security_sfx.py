import pytest
from fastapi.testclient import TestClient
from studio.app import app
from unittest.mock import patch, AsyncMock
import os

client = TestClient(app)

@patch("studio.app.sfx_generator.generate", new_callable=AsyncMock)
def test_generate_sfx_path_traversal(mock_generate):
    """Test that path traversal attempts in story_name are rejected.

    The endpoint uses safe_join(OUTPUT_DIR, request.story_name), which
    raises ValueError when the resolved path would escape OUTPUT_DIR; the
    endpoint catches that and returns an error *before* ever creating a
    directory. Verified directly: os.makedirs is never called, and no
    audio generation is attempted.
    """
    payload = {
        "text": "footsteps",
        "story_name": "../../../secrets"
    }

    with patch("os.makedirs") as mock_makedirs:
        response = client.post("/api/generate_sfx", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Invalid story name" in data["message"]

        # The rejection happens before any directory is created or any
        # audio is generated -- the traversal path is never touched.
        mock_makedirs.assert_not_called()
        mock_generate.assert_not_called()
