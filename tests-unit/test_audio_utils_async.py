import pytest
import asyncio
import json
import os
import shutil
from scripts.audio_utils import ComfyAudioGenerator

@pytest.mark.asyncio
async def test_generate_sfx_async_httpx(httpx_mock, monkeypatch):
    """
    Test that ComfyAudioGenerator.generate uses httpx for requests
    and handles the flow correctly.
    """
    # Mock ComfyUI URL
    comfy_url = "http://127.0.0.1:8188"
    prompt_url = f"{comfy_url}/prompt"
    history_url = f"{comfy_url}/history"
    
    # Mock Response Data
    prompt_id = "test_prompt_123"
    filename = "sfx_generated.wav"
    subfolder = "audio/sfx"
    
    # 1. Mock the /prompt endpoint (POST)
    httpx_mock.add_response(
        method="POST",
        url=prompt_url,
        json={"prompt_id": prompt_id},
        status_code=200
    )
    
    # 2. Mock the /history endpoint (GET)
    # We need to match the history URL with the specific prompt_id
    history_data = {
        prompt_id: {
            "outputs": {
                "21": {
                    "audio": [
                        {
                            "filename": filename,
                            "subfolder": subfolder,
                            "type": "output"
                        }
                    ]
                }
            }
        }
    }
    
    httpx_mock.add_response(
        method="GET",
        url=f"{history_url}/{prompt_id}",
        json=history_data,
        status_code=200
    )

    # Mock Filesystem operations
    # We want to avoid real FS access
    
    def mock_makedirs(path, exist_ok=False):
        pass
    
    def mock_path_exists(path):
        # Pretend the file exists
        return True
        
    def mock_move(src, dst):
        pass
        
    def mock_abspath(path):
        return path
        
    monkeypatch.setattr(os, "makedirs", mock_makedirs)
    monkeypatch.setattr(os.path, "exists", mock_path_exists)
    monkeypatch.setattr(shutil, "move", mock_move)
    # monkeypatch.setattr(os.path, "abspath", mock_abspath) # Keep real abspath if possible, or mock carefully

    # Initialize Generator
    generator = ComfyAudioGenerator(comfy_url=comfy_url)
    
    # Define output path
    output_path = "/tmp/test_sfx.wav"
    
    # Execute
    result = await generator.generate("Test Prompt", output_path)
    
    # Assertions
    assert result == output_path
    
    # Check httpx requests
    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    assert requests[0].method == "POST"
    assert requests[0].url == prompt_url
    assert requests[1].method == "GET"
    assert str(requests[1].url) == f"{history_url}/{prompt_id}"