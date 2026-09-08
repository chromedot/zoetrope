import unittest
import os
import shutil
import tempfile
from scripts.video_utils import VideoStitcher, SimpleCutStrategy

class TestVideoStitcher(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        self.stitcher = VideoStitcher(output_root=self.output_dir)
        
        # Create some dummy image files
        self.image_files = []
        for i in range(3):
            path = os.path.join(self.test_dir, f"scene_{i:02d}_00001_.png")
            with open(path, "wb") as f:
                f.write(b"dummy image data")
            self.image_files.append(path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.output_dir)

    def test_generate_ffmpeg_command_simple(self):
        """Test generating a simple ffmpeg command without complex transitions."""
        # _build_ffmpeg_command was replaced by the Strategy-pattern refactor
        # (VideoStitcher.stitch() dispatches to a TransitionStrategy subclass);
        # "none" maps to SimpleCutStrategy.
        output_path = os.path.join(self.output_dir, "test.mp4")
        strategy = SimpleCutStrategy(self.output_dir)
        cmd = strategy.build_command(self.image_files, output_path, duration=2.0)

        # Check for key parts of the command
        self.assertIn("ffmpeg", cmd)
        self.assertIn("-i", cmd)
        self.assertIn(output_path, cmd)
        # Concat demuxer uses a single input file list
        self.assertEqual(cmd.count("-i"), 1)

    def test_output_path_generation(self):
        """Test that output path is correctly formatted."""
        story_name = "test_story"
        path = self.stitcher.get_output_path(story_name)
        self.assertIn(story_name, path)
        self.assertIn(self.output_dir, path)
        self.assertTrue(path.endswith(".mp4"))

if __name__ == "__main__":
    unittest.main()
