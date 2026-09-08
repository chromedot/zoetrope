import unittest
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.audio_utils import ComfyAudioGenerator

class TestAudioUpgrade(unittest.TestCase):
    def test_workflow_structure(self):
        """Verify the workflow generator uses the new AudioLDM2-Large model and FP8."""
        generator = ComfyAudioGenerator()
        workflow = generator._get_workflow("Test Prompt")
        
        # Check Node 19 (AudioLDM)
        self.assertIn("19", workflow)
        node_inputs = workflow["19"]["inputs"]
        
        self.assertEqual(node_inputs["model_id"], "cvssp/audioldm2-large", "Should use AudioLDM2-Large")
        self.assertEqual(node_inputs["precision"], "fp8", "Should use FP8 precision")
        self.assertEqual(node_inputs["prompt"], "Test Prompt", "Prompt should be injected")
        
        # Check Node 21 (SaveAudioLDM)
        self.assertIn("21", workflow)
        self.assertEqual(workflow["21"]["inputs"]["output_folder_name"], "audio/sfx")

if __name__ == '__main__':
    unittest.main()