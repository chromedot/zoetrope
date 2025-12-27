import pytest
import os
import json
import shutil
import tempfile
import httpx
from scripts.audio_utils import ComfyAudioGenerator

@pytest.fixture
def temp_output_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

@pytest.mark.asyncio
async def test_comfy_audio_generator_success(httpx_mock, temp_output_dir):
    generator = ComfyAudioGenerator(comfy_url="http://localhost:8188")
    
    # Mock /prompt
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8188/prompt",
        json={"prompt_id": "test-prompt-id"}
    )
    
    # Mock /history/test-prompt-id
    httpx_mock.add_response(
        method="GET",
        url="http://localhost:8188/history/test-prompt-id",
        json={
            "test-prompt-id": {
                "outputs": {
                    "21": {
                        "audio": [
                            {
                                "filename": "test.wav",
                                "subfolder": "audio/sfx",
                                "type": "output"
                            }
                        ]
                    }
                }
            }
        }
    )
    
    # Setup dummy source file that generator expects to find and move
    comfy_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    comfy_output_dir = os.path.join(comfy_root, "output", "audio", "sfx")
    os.makedirs(comfy_output_dir, exist_ok=True)
    dummy_source = os.path.join(comfy_output_dir, "test.wav")
    with open(dummy_source, "wb") as f:
        f.write(b"dummy audio")
        
    output_path = os.path.join(temp_output_dir, "result.wav")
    
    try:
        result = await generator.generate("test prompt", output_path)
        
        assert result == output_path
        assert os.path.exists(output_path)
        with open(output_path, "rb") as f:
            assert f.read() == b"dummy audio"
    finally:
        if os.path.exists(dummy_source):
            os.remove(dummy_source)

@pytest.mark.asyncio
async def test_comfy_audio_generator_timeout(httpx_mock, temp_output_dir):
    # Set a very short timeout for testing
    generator = ComfyAudioGenerator(comfy_url="http://localhost:8188", timeout=0.1)
    
    # Mock /prompt
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8188/prompt",
        json={"prompt_id": "timeout-id"}
    )
    
    # Mock /history/timeout-id with empty response (still polling)
    # We use a callback or ensure it can be called multiple times.
    # pytest-httpx default behavior consumes response. 
    # We can use a regex or just add many responses, but callback is cleaner.
    
    def history_callback(request):
        return httpx.Response(status_code=200, json={})

    httpx_mock.add_callback(
        callback=history_callback,
        method="GET",
        url="http://localhost:8188/history/timeout-id"
    )
    
    output_path = os.path.join(temp_output_dir, "result.wav")
    
    with pytest.raises(TimeoutError):
        await generator.generate("test prompt", output_path)
