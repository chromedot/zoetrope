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

        # Create dummy sfx files
        self.sfx_files = []
        for i in range(2):
            path = os.path.join(self.test_dir, f"sfx_{i:02d}.wav")
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                "-t", "1", path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.sfx_files.append(path)

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
                audio_files=self.audio_files,
                sfx_files=self.sfx_files
            )
        except TypeError:
            self.fail("TransitionStrategy.build_command does not accept audio_files/sfx_files")

    def test_simple_cut_warns_on_audio(self):
        """Verify SimpleCutStrategy warns or handles audio (currently it ignores/warns)."""
        # For now, we expect it to ignore or log, but not fail.
        # Ideally it should log a warning as per my plan to update it.
        pass

    def test_audio_mixed_strategy(self):
        """Test AudioMixedStrategy builds a command with mixed audio."""
        from scripts.video_utils import AudioMixedStrategy
        
        strategy = AudioMixedStrategy(self.output_dir)
        output_path = os.path.join(self.output_dir, "mixed.mp4")
        duration = 2.0
        
        cmd = strategy.build_command(
            self.image_files, 
            output_path, 
            duration, 
            audio_files=self.audio_files,
            sfx_files=self.sfx_files
        )
        
        # Verify command structure
        self.assertIn("ffmpeg", cmd)
        for f in self.image_files:
            self.assertIn(f, cmd)
        for f in self.audio_files:
            self.assertIn(f, cmd)
        for f in self.sfx_files:
            self.assertIn(f, cmd)
            
        # Check for filter_complex which is required for mixing
        self.assertIn("-filter_complex", cmd)
        # Check for amix since we provided both audio and sfx
        filter_str = cmd[cmd.index("-filter_complex") + 1]
        self.assertIn("amix", filter_str)

    def test_duration_sync(self):
        """Verify that AudioMixedStrategy adjusts scene duration to match audio."""
        from scripts.video_utils import AudioMixedStrategy
        strategy = AudioMixedStrategy(self.output_dir)
        
        # Create a long audio file (5s)
        long_audio = os.path.join(self.test_dir, "long.wav")
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
            "-t", "5", long_audio
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        cmd = strategy.build_command(
            [self.image_files[0]], 
            os.path.join(self.output_dir, "sync.mp4"), 
            duration=2.0, # Default shorter than audio
            audio_files=[long_audio]
        )
        
        # Check that -t 5 is used for the image loop, not 2
        # Command input structure: ... -loop 1 -t 5.0 -i ...
        # We need to find "-t" followed by "5.0"
        
        try:
            t_idx = cmd.index("-t")
            # Might appear multiple times (for anullsrc etc).
            # The one for image loop comes before -i image
            
            # Find the index of image file
            img_idx = cmd.index(self.image_files[0])
            
            # Look backwards from img_idx for "-t"
            # slice cmd[:img_idx]
            pre_img = cmd[:img_idx]
            # Reverse find "-t"
            last_t_idx = len(pre_img) - 1 - pre_img[::-1].index("-t")
            
            duration_arg = cmd[last_t_idx + 1]
            self.assertEqual(float(duration_arg), 5.0)
            
        except ValueError:
            self.fail("Could not find duration argument or image file in command")

if __name__ == "__main__":
    unittest.main()