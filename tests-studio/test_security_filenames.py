import pytest
import uuid
import re
from scripts.audio_utils import ComfyAudioGenerator
from studio.app import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_uuid_filename_pattern():
    """
    Test that generated filenames contain a UUID.
    This is a bit tricky to test end-to-end without running the whole flow,
    but we can mock the generator or check the implementation logic via unit tests.
    
    For now, let's verify that the endpoints return filenames matching a UUID pattern.
    """
    # We can use the mock sfx generation from the earlier test to see what filename it returns.
    # But wait, app.py constructs the filename BEFORE calling the generator.
    # So if we mock the generator to just succeed, we can check the returned filename.
    pass

@pytest.mark.asyncio
async def test_sfx_filename_is_uuid(httpx_mock, monkeypatch):
    """
    Test that /api/generate_sfx returns a UUID-based filename.
    """
    # Mock ComfyAudioGenerator.generate to avoid actual work
    async def mock_generate(*args, **kwargs):
        return
        
    # We need to patch the sfx_generator instance in app.py
    # This is hard because it's already instantiated.
    # We can patch the method on the class or the instance.
    
    from studio.app import sfx_generator
    monkeypatch.setattr(sfx_generator, "generate", mock_generate)
    
    payload = {
        "text": "uuid test",
        "story_name": "test_story"
    }
    
    # We also need to ensure output dir exists or mock os.makedirs
    import os
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: None)
    
    response = client.post("/api/generate_sfx", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    filename = data.get("filename")
    assert filename is not None
    
    assert "sfx_" in filename

    # Actual format (studio/app.py generate_sfx): sfx_<8-hex-char short uuid>.wav
    import re
    match = re.search(r'sfx_[0-9a-f]{8}\.wav', filename)
    assert match is not None, f"Filename {filename} does not contain an 8-char hex UUID"

@pytest.mark.asyncio
async def test_tts_filename_is_uuid(httpx_mock, monkeypatch):
    from studio.app import tts_generator, manager
    
    async def mock_generate(*args, **kwargs):
        return
    monkeypatch.setattr(tts_generator, "generate", mock_generate)
    monkeypatch.setattr(manager, "save_story", lambda: None)
    
    # Mock DB update
    from studio import database
    monkeypatch.setattr(database, "update_scene_narration", lambda *args: None)
    
    # Mock Story Data
    manager.story_data = [{"scene": 1, "description": "test scene"}]
    
    payload = {
        "scene_index": 0,
        "text": "test",
        "story_name": "test_story"
    }
    
    response = client.post("/api/generate_audio", json=payload)
    assert response.status_code == 200
    data = response.json()
    filename = data.get("filename")
    
    # Format: scene_<index>_<short_uuid>.mp3
    match = re.search(r'scene_\d{2}_[0-9a-f]{8}\.mp3', filename)
    assert match is not None, f"Filename {filename} does not contain an 8-char hex UUID"
