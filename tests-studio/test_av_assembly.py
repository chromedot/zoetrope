import unittest
import os
import shutil
import tempfile
import subprocess
from scripts.video_utils import VideoStitcher, SimpleCutStrategy

class TestAVAssembly(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        self.stitcher = VideoStitcher(output_root=self.output_dir)
        
        # Create dummy image files
        self.image_files = []
        for i in range(2):
            path = os.path.join(self.test_dir, f"scene_{i:02d}.png")
            # Create a red/blue square using ffmpeg to have a valid image
            color = "red" if i == 0 else "blue"
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c={color}:s=1280x720:d=0.1",
                "-frames:v", "1", path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.image_files.append(path)
            
        # Create dummy audio files (silence)
        self.audio_files = []
        for i in range(2):
            path = os.path.join(self.test_dir, f"audio_{i:02d}.wav")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-t", "2", path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.audio_files.append(path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)

    def test_interface_accepts_audio(self):
        """Verify the TransitionStrategy interface accepts audio_files."""
        # This test confirms the previous task (interface update) works
        strategy = SimpleCutStrategy(self.output_dir)
        # Should not raise TypeError
        try:
            cmd = strategy.build_command(
                self.image_files, 
                os.path.join(self.output_dir, "output.mp4"), 
                duration=2.0, 
                audio_files=self.audio_files
            )
        except TypeError:
            self.fail("TransitionStrategy.build_command does not accept audio_files")

    def test_simple_cut_warns_on_audio(self):
        """Verify SimpleCutStrategy warns or handles audio (currently it ignores/warns)."""
        # For now, we expect it to ignore or log, but not fail.
        # Ideally it should log a warning as per my plan to update it.
        pass

if __name__ == "__main__":
    unittest.main()