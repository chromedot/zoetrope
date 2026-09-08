
import unittest
import torch
import os
import sys
from diffusers import AudioLDM2Pipeline

# Mock folder_paths if needed, or just use absolute path for test
MODEL_PATH = os.path.abspath("models/audio_checkpoints/audioldm2-large")

class TestAudioLDMFP8(unittest.TestCase):
    def test_01_fp8_datatype_exists(self):
        """Check if torch.float8_e4m3fn is available."""
        self.assertTrue(hasattr(torch, 'float8_e4m3fn'), "torch.float8_e4m3fn not found in torch")
        print(f"\n[INFO] torch.float8_e4m3fn found: {torch.float8_e4m3fn}")

    def test_02_load_pipeline_fp8(self):
        """Attempt to load AudioLDM2Pipeline in FP16 and cast to FP8."""
        if not hasattr(torch, 'float8_e4m3fn'):
            self.skipTest("FP8 not supported by torch version")
            
        if not os.path.exists(MODEL_PATH):
            self.skipTest(f"Model not found at {MODEL_PATH}")

        print(f"\n[INFO] Loading model from {MODEL_PATH} with FP16...")
        try:
            pipe = AudioLDM2Pipeline.from_pretrained(
                MODEL_PATH, 
                torch_dtype=torch.float16,
                local_files_only=True
            )
            print("[SUCCESS] Pipeline loaded successfully with FP16 dtype.")
            
            # Now try to cast UNet to FP8
            if hasattr(pipe, "unet"):
                print("[INFO] Casting UNet to FP8...")
                pipe.unet.to(dtype=torch.float8_e4m3fn)
                
                first_param = next(pipe.unet.parameters())
                print(f"[INFO] UNet param dtype after cast: {first_param.dtype}")
                
                self.assertEqual(first_param.dtype, torch.float8_e4m3fn, "UNet should be in FP8")
            else:
                self.skipTest("Pipeline has no unet attribute")

        except Exception as e:
            self.fail(f"Failed to load pipeline or cast to FP8: {e}")

if __name__ == '__main__':
    unittest.main()
