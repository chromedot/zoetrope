import pytest
from fastapi.testclient import TestClient
from studio.app import app
import os
import shutil

client = TestClient(app)

def test_dynamic_story_sfx(httpx_mock, monkeypatch):
    """
    Test that /api/generate_sfx uses the story_name from the request.
    """
    async def mock_generate(*args, **kwargs):
        return
    from studio.app import sfx_generator
    monkeypatch.setattr(sfx_generator, "generate", mock_generate)
    monkeypatch.setattr(os, "makedirs", lambda *args, **kwargs: None)
    
    story_name = "aliens_invade"
    payload = {
        "text": "laser sound",
        "story_name": story_name
    }
    
    response = client.post("/api/generate_sfx", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Check that audio_url contains the dynamic story name
    assert f"/images/{story_name}/audio/" in data.get("audio_url")

def test_dynamic_story_audio(httpx_mock, monkeypatch):
    """
    Test that /api/generate_audio uses the story_name from the request.
    """
    async def mock_generate(*args, **kwargs):
        return
    from studio.app import tts_generator, manager
    monkeypatch.setattr(tts_generator, "generate", mock_generate)
    monkeypatch.setattr(manager, "save_story", lambda: None)
    
    # Mock DB update
    from studio import database
    monkeypatch.setattr(database, "update_scene_narration", lambda *args: None)
    
    story_name = "future_war"
    # manager.story_data should ideally be loaded based on story_name,
    # but currently app.py has a global 'manager' instance for 'geronimo'.
    # This task involves making it dynamic. 
    # For now, let's see if the API respects the story_name in the URL/DB call.
    
    payload = {
        "scene_index": 0,
        "text": "The year is 2077",
        "story_name": story_name
    }
    
    # We might need to mock manager.story_data if it's used for validation
    manager.story_data = [{"scene": 1, "description": "intro"}]
    
    response = client.post("/api/generate_audio", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert f"/images/{story_name}/audio/" in data.get("audio_url")
