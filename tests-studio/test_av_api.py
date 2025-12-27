import unittest
import os
import json
import shutil
from fastapi.testclient import TestClient
from studio.app import app
import database

from unittest.mock import patch

class TestAVAPI(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "data/test_av_api.db"
        database.DB_PATH = self.test_db_path
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        database.init_db()
        
        # Setup Test Story
        self.test_story_dir = "data/stories"
        os.makedirs(self.test_story_dir, exist_ok=True)
        self.story_name = "test_fetch_audio"
        self.story_path = os.path.join(self.test_story_dir, f"{self.story_name}.story")
        
        # Create a story with 2 scenes, each having image, audio, and sfx
        self.story_data = [
            {
                "scene": 0, 
                "description": "Scene 1", 
                "image_path": f"{self.story_name}/scene_00_img.png",
                "audio_file": f"{self.story_name}/scene_00_narration.wav",
                "sfx_file": f"{self.story_name}/scene_00_sfx.wav"
            },
            {
                "scene": 1, 
                "description": "Scene 2", 
                "image_path": f"{self.story_name}/scene_01_img.png",
                # Scene 1 has no audio/sfx to test sparse data
            }
        ]
        with open(self.story_path, "w") as f:
            json.dump(self.story_data, f)
            
        self.client = TestClient(app)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.story_path):
            os.remove(self.story_path)

    def test_video_request_model_extended(self):
        """Test that the VideoRequest model accepts audio_files and sfx_files."""
        payload = {
            "story_name": "test_story",
            "files": ["img1.png"],
            "transition": "audio_mixed",
            "duration": 2.0,
            "audio_files": ["aud1.wav"],
            "sfx_files": ["sfx1.wav"]
        }
        
        response = self.client.post("/api/generate_video", json=payload)
        self.assertEqual(response.status_code, 200)

    @patch("studio.app.perform_stitching")
    def test_generate_video_fetches_audio(self, mock_stitch):
        """Test that generate_video fetches audio/sfx from story manager if not provided."""
        
        # Request only images
        payload = {
            "story_name": self.story_name,
            "files": [
                f"{self.story_name}/scene_00_img.png",
                f"{self.story_name}/scene_01_img.png"
            ],
            "transition": "audio_mixed",
            "duration": 2.0
        }
        
        response = self.client.post("/api/generate_video", json=payload)
        self.assertEqual(response.status_code, 200)
        
        # Verify perform_stitching was called
        self.assertTrue(mock_stitch.called)
        
        # Check args
        # call_args[1] is kwargs. 
        # We expect audio_files and sfx_files to be populated based on story data.
        # Scene 0: has audio and sfx
        # Scene 1: has None
        
        call_kwargs = mock_stitch.call_args[1]
        
        expected_audio = [
            f"{self.story_name}/scene_00_narration.wav",
            None
        ]
        expected_sfx = [
            f"{self.story_name}/scene_00_sfx.wav",
            None
        ]
        
        # Note: Paths might be absolute or relative depending on implementation.
        # But initially we stored them as relative in story_data.
        # The fetch logic usually keeps them as stored or resolves them.
        # Let's check what we get.
        
        # Adjust expectation: logic usually resolves full path? 
        # Or relative?
        # VideoStitcher handles paths. 
        # If app.py fetches from manager, it gets what is in JSON.
        
        self.assertEqual(call_kwargs['audio_files'], expected_audio)
        self.assertEqual(call_kwargs['sfx_files'], expected_sfx)

    @patch("studio.app.perform_stitching")
    def test_generate_video_disables_audio(self, mock_stitch):
        """Test that passing empty lists for audio_files disables fetching."""
        payload = {
            "story_name": self.story_name,
            "files": [f"{self.story_name}/scene_00_img.png"],
            "transition": "audio_mixed",
            "duration": 2.0,
            "audio_files": [], # Explicitly disabled
            "sfx_files": []   # Explicitly disabled
        }
        
        response = self.client.post("/api/generate_video", json=payload)
        self.assertEqual(response.status_code, 200)
        
        call_kwargs = mock_stitch.call_args[1]
        self.assertEqual(call_kwargs['audio_files'], [])
        self.assertEqual(call_kwargs['sfx_files'], [])

if __name__ == "__main__":
    unittest.main()