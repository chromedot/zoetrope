import pytest
from fastapi.testclient import TestClient
from studio.app import app
from unittest.mock import patch, AsyncMock
import os

client = TestClient(app)

@patch("studio.app.sfx_generator.generate", new_callable=AsyncMock)
def test_generate_sfx_path_traversal(mock_generate):
    """Test that path traversal attempts in story_name are sanitized or rejected."""
    
    # We want to ensure that "output/../secrets/audio/filename" is NOT created.
    # The vulnerability was: audio_dir = os.path.join(OUTPUT_DIR, request.story_name, "audio")
    
    payload = {
        "text": "footsteps",
        "story_name": "../../../secrets" 
    }
    
    # We mock the actual generation to avoid calling ComfyUI, 
    # but we want to check the path that was passed to it or created.
    # However, the vulnerability is in os.makedirs(audio_dir) inside the endpoint
    # BEFORE calling generator.
    
    # We can mock os.makedirs to verify the path it receives.
    with patch("os.makedirs") as mock_makedirs:
        response = client.post("/api/generate_sfx", json=payload)
        
        # We expect the current implementation to attempt to create the malicious path
        # leading to a security issue.
        # But since we are writing a FAILING test for the remediation,
        # we assert that it SHOULD FAIL to create that path or sanitize it.
        
        # Wait, TDD says write a failing test.
        # The CURRENT behavior ALLOWS traversal.
        # So a test that asserts "Traversal is blocked" will FAIL.
        
        # Let's inspect what makedirs was called with.
        # If traversal is BLOCKED, makedirs should be called with something safe,
        # or the endpoint should return an error.
        
        # Let's assume we want to sanitize it to "secrets" or just reject it.
        # The spec says "Sanitize ... Prevent directory traversal".
        
        # If we assert that the path does NOT contain "..", the test will fail on the current code.
        
        assert response.status_code == 200 # It might still return 200 if we just sanitize
        
        # Get the path passed to makedirs
        args, _ = mock_makedirs.call_args
        created_dir = args[0]
        
        # We want to ensure the resolved path is inside OUTPUT_DIR
        # For the failing test, we assert that it IS safe. 
        # Since currently it is NOT safe, this assertion will FAIL.
        
        assert ".." not in created_dir
        # It should end with /secrets/audio (because basename kept 'secrets')
        # but it should be rooted in OUTPUT_DIR
        assert created_dir.endswith("/secrets/audio")
