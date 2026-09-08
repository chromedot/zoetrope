import os
import asyncio
import logging
import edge_tts
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

import os
import asyncio
import logging
import edge_tts
import json
import httpx
import time
import random
import uuid
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

class ComfyAudioGenerator(AudioGenerator):
    """Implementation using ComfyUI AudioLDM node."""
    
    def __init__(self, comfy_url="http://127.0.0.1:8188", timeout=120):
        self.comfy_url = comfy_url
        self.prompt_url = f"{comfy_url}/prompt"
        self.history_url = f"{comfy_url}/history"
        self.timeout = timeout

    async def generate(self, text: str, output_path: str, voice: str = None):
        """
        Generates audio using ComfyUI AudioLDM.
        'voice' parameter is ignored here, used as seed/style if needed?
        output_path: Expected to be full path. We will try to make Comfy save there 
                     or move it there.
        """
        logger.info(f"Generating SFX for prompt: {text[:50]}...")
        
        # 1. Determine Output details
        # ComfyUI saves relative to its output directory.
        # We need to extract the subfolder from output_path relative to Comfy output.
        # Assuming output_path is like <PROJECT_ROOT>/output/story_name/audio/filename.wav
        
        # We'll use a standard template workflow
        workflow = self._get_workflow(text)
        
        # We need to configure the SaveAudioLDM node to save to a specific subfolder if possible.
        # The node has 'output_folder_name'. 
        # Let's try to deduce the relative path.
        
        # Quick hack: We let Comfy save to "audio/sfx" and then we move/rename to output_path.
        # This is safer than trying to force Comfy to write to absolute paths.
        
        short_uuid = str(uuid.uuid4())[:8]
        filename_prefix = f"sfx_{short_uuid}"
        
        # Update Workflow
        workflow["21"]["inputs"]["filename_prefix"] = filename_prefix
        workflow["21"]["inputs"]["output_folder_name"] = "audio/sfx"
        
        async with httpx.AsyncClient() as client:
            # 2. Submit to ComfyUI
            prompt_id = await self._queue_prompt(client, workflow)
            logger.info(f"ComfyUI SFX task queued: {prompt_id}")
            
            # 3. Poll for completion
            history = await self._wait_for_history(client, prompt_id, timeout=self.timeout)
        
        # 4. Locate the file
        # History structure: { prompt_id: { "outputs": { "21": { "audio": [ { "filename": ..., "subfolder": ..., "type": ... } ] } } } }
        try:
            outputs = history[prompt_id]['outputs']['21']['audio'][0]
            generated_filename = outputs['filename']
            subfolder = outputs['subfolder']
            
            # Construct where Comfy saved it
            comfy_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            comfy_output_dir = os.path.join(comfy_root, "output")
            
            # Try 1: Trust the returned subfolder
            source_path = os.path.join(comfy_output_dir, subfolder, generated_filename)
            
            # Try 2: If not found, check our expected folder "audio/sfx"
            if not os.path.exists(source_path):
                source_path_alt = os.path.join(comfy_output_dir, "audio", "sfx", generated_filename)
                if os.path.exists(source_path_alt):
                    source_path = source_path_alt
            
            # 5. Move to requested output_path
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Check if source exists
            if os.path.exists(source_path):
                import shutil
                # Ensure we don't overwrite if it's the same file (edge case)
                if os.path.abspath(source_path) != os.path.abspath(output_path):
                    shutil.move(source_path, output_path)
                logger.info(f"Moved SFX to: {output_path}")
                return output_path
            else:
                logger.error(f"Generated file not found at {source_path} (Subfolder: {subfolder})")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing ComfyUI response: {e}")
            raise e

    async def _queue_prompt(self, client, workflow):
        p = {"prompt": workflow}
        # httpx handles json encoding automatically
        response = await client.post(self.prompt_url, json=p)
        response.raise_for_status()
        return response.json()['prompt_id']

    async def _wait_for_history(self, client, prompt_id, timeout=120):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await client.get(f"{self.history_url}/{prompt_id}")
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        return history
            except Exception as e:
                # Log warning but continue polling
                # logger.warning(f"Error polling history: {e}")
                pass
            await asyncio.sleep(1)
        raise TimeoutError("Timed out waiting for ComfyUI generation")

    def _get_workflow(self, prompt_text):
        # Load from template
        workflow_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "workflows", "audioldm2_fp8.json")
        try:
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
            
            # Inject parameters
            workflow["19"]["inputs"]["prompt"] = prompt_text
            workflow["19"]["inputs"]["seed"] = random.randint(1, 1000000000000)
            
            return workflow
        except Exception as e:
            logger.error(f"Failed to load workflow template: {e}")
            # Fallback
            return {
                "19": {
                    "inputs": {
                        "prompt": prompt_text,
                        "model_id": "cvssp/audioldm2-large",
                        "precision": "fp8",
                        "audio_length": 5.0,
                        "num_steps": 25,
                        "sample_rate": 44100,
                        "seed": random.randint(1, 1000000000000)
                    },
                    "class_type": "AudioLDM",
                    "_meta": {
                        "title": "AudioLDM"
                    }
                },
                "21": {
                    "inputs": {
                        "audio": [
                            "19",
                            0
                        ],
                        "filename_prefix": "sfx",
                        "output_folder_name": "audio"
                    },
                    "class_type": "SaveAudioLDM",
                    "_meta": {
                        "title": "SaveAudioLDM"
                    }
                }
            }

# Helper to run async from sync code if needed
def generate_audio_sync(text: str, output_path: str, voice: str = None):
    generator = EdgeTTSGenerator()
    return asyncio.run(generator.generate(text, output_path, voice))
