import pytest
import os
from unittest.mock import MagicMock, patch, AsyncMock
from scripts.audio_utils import EdgeTTSGenerator, generate_audio_sync

@pytest.mark.asyncio
async def test_edge_tts_generator_success():
    """Test successful audio generation with mocked edge-tts."""
    generator = EdgeTTSGenerator()
    text = "Hello world"
    output_path = "/tmp/test.mp3"
    
    # Mock edge_tts.Communicate
    with patch("edge_tts.Communicate") as MockCommunicate, \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=True):
        
        # Setup mock instance
        mock_instance = MockCommunicate.return_value
        mock_instance.save = AsyncMock()
        
        result = await generator.generate(text, output_path)
        
        # Verify calls
        MockCommunicate.assert_called_with(text, "en-US-GuyNeural")
        mock_instance.save.assert_called_with(output_path)
        assert result == output_path

@pytest.mark.asyncio
async def test_edge_tts_generator_failure():
    """Test handling of failures in edge-tts generation."""
    generator = EdgeTTSGenerator()
    
    with patch("edge_tts.Communicate") as MockCommunicate, \
         patch("os.makedirs"):
        
        mock_instance = MockCommunicate.return_value
        mock_instance.save = AsyncMock(side_effect=Exception("Connection error"))
        
        with pytest.raises(Exception, match="Audio generation failed: Connection error"):
            await generator.generate("fail", "out.mp3")

def test_generate_audio_sync_helper():
    """Test the sync wrapper helper."""
    with patch("scripts.audio_utils.EdgeTTSGenerator.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = "sync_out.mp3"
        
        result = generate_audio_sync("sync test", "sync_out.mp3")
        
        assert result == "sync_out.mp3"
        mock_gen.assert_called()
