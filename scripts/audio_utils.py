import os
import asyncio
import logging
import edge_tts
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AudioGenerator(ABC):
    """Abstract base class for Audio generation (TTS)."""
    @abstractmethod
    async def generate(self, text: str, output_path: str, voice: str = None):
        """Generates an audio file from text."""
        pass

class EdgeTTSGenerator(AudioGenerator):
    """Implementation using edge-tts library."""
    
    def __init__(self, default_voice: str = "en-US-GuyNeural"):
        self.default_voice = default_voice

    async def generate(self, text: str, output_path: str, voice: str = None):
        """Generates audio using Edge TTS."""
        voice = voice or self.default_voice
        logger.info(f"Generating audio for text: {text[:50]}... with voice {voice}")
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_path)
            
            if os.path.exists(output_path):
                logger.info(f"Successfully generated audio at: {output_path}")
                return output_path
            else:
                logger.error("Audio file was not created.")
                return None
                
        except Exception as e:
            logger.error(f"Edge TTS generation failed: {e}")
            raise Exception(f"Audio generation failed: {str(e)}")

# Helper to run async from sync code if needed
def generate_audio_sync(text: str, output_path: str, voice: str = None):
    generator = EdgeTTSGenerator()
    return asyncio.run(generator.generate(text, output_path, voice))
