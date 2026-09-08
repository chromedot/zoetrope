import pytest
from fastapi.testclient import TestClient
from studio.app import app
import os

client = TestClient(app)

def test_check_status_path_traversal():
    # Attempt to access a file outside the allowed directory
    # Expected behavior: Should fail or return ready: False
    
    # We try to look for /etc/passwd or similar (mocked relative)
    # The vulnerability allows reading if we can guess the prefix
    
    # In check_status:
    # folder, file_prefix = os.path.split(prefix)
    # search_path = os.path.join(OUTPUT_DIR, folder, file_prefix + "*.png")
    
    # If we pass prefix="../../etc/passwd", folder is "../../etc", file_prefix is "passwd"
    # joined: <PROJECT_ROOT>/output/../../etc/passwd*.png -> <PROJECT_ROOT>/etc/passwd*.png (still inside project, but outside output)
    # If we go deeper: "../../../../../etc/passwd"
    
    response = client.get("/api/check_status?prefix=../../../../../etc/passwd")
    assert response.status_code == 200
    assert response.json() == {"ready": False}

def test_generate_audio_path_traversal():
    # Attempt to write to an arbitrary location
    # request.story_name is used in path construction:
    # audio_dir = os.path.join(OUTPUT_DIR, request.story_name, "audio")
    
    payload = {
        "scene_index": 0,
        "text": "Security test",
        "story_name": "../../../tmp/hacked_story"
    }
    
    # We expect this to fail or sanitize the path
    # Currently it might succeed in creating /tmp/hacked_story/audio if not secured
    
    # To test this safely without actually writing to /tmp if we can avoid it, 
    # we can check if the code sanitizes it. 
    # But for a "Red" test, we expect the vulnerability to be present (or we assume it is).
    # If the vulnerability IS present, this might actually write to /tmp.
    
    # Let's assert that it fails safely.
    response = client.post("/api/generate_audio", json=payload)
    
    # Ideally, we want a 400 error or a sanitized path.
    # If it returns success but wrote to /tmp, that's a fail.
    # If we can't easily check FS side effects, we check the returned URL.
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            # Check where it thinks it wrote
            # If it says "/images/../../../tmp/...", that's bad.
            assert "../" not in data.get("audio_url", ""), "Path traversal detected in response URL"
            assert "/tmp/" not in data.get("audio_url", ""), "Path traversal detected in response URL"

def test_generate_sfx_path_traversal():
    payload = {
        "text": "Security test",
        "story_name": "../../../tmp/hacked_story_sfx"
    }
    
    response = client.post("/api/generate_sfx", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("status") == "success":
            assert "../" not in data.get("audio_url", ""), "Path traversal detected in response URL"
