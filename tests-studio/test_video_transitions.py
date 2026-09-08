import pytest
from unittest.mock import MagicMock, patch, ANY
from scripts.video_utils import VideoStitcher

# We'll need to import these in the implementation, so we mock/import them here
# assuming they will exist in video_utils or a new module.
# For now, we test the refactored VideoStitcher behavior.

def test_stitcher_uses_simple_cut_strategy_by_default():
    """Test that 'none' transition uses the simple concat strategy."""
    stitcher = VideoStitcher()
    files = ["/tmp/1.png", "/tmp/2.png"]
    
    # We mock the internal method or strategy to verify it's called.
    # Since we are refactoring, we expect a SimpleCutStrategy class eventually.
    # For this Red phase, we'll verify the current behavior is maintained 
    # OR better, we expect the NEW structure.
    
    # Let's write the test for the NEW structure we want.
    # We want stitcher to delegate.
    
    with patch("scripts.video_utils.SimpleCutStrategy") as MockStrategy, \
         patch("subprocess.run") as mock_run:
        strategy_instance = MockStrategy.return_value
        strategy_instance.build_command.return_value = ["ffmpeg", "dummy"]
        
        stitcher.stitch(files, "story", transition="none")

        # Verify Strategy was initialized and called
        MockStrategy.assert_called()
        # stitch() always passes audio_files/sfx_files through (None here, since
        # the call above doesn't set them) -- see VideoStitcher.stitch().
        strategy_instance.build_command.assert_called_with(files, ANY, 2.0, audio_files=None, sfx_files=None)
        mock_run.assert_called_with(["ffmpeg", "dummy"], check=True, capture_output=True)

def test_stitcher_uses_crossfade_strategy():
    """Test that 'crossfade' transition uses the CrossFadeStrategy."""
    stitcher = VideoStitcher()
    files = ["/tmp/1.png", "/tmp/2.png"]
    
    with patch("scripts.video_utils.CrossFadeStrategy") as MockStrategy, \
         patch("subprocess.run") as mock_run:
        strategy_instance = MockStrategy.return_value
        strategy_instance.build_command.return_value = ["ffmpeg", "dummy_xfade"]
        
        stitcher.stitch(files, "story", transition="crossfade")

        MockStrategy.assert_called()
        strategy_instance.build_command.assert_called_with(files, ANY, 2.0, audio_files=None, sfx_files=None)
        mock_run.assert_called_with(["ffmpeg", "dummy_xfade"], check=True, capture_output=True)

def test_stitcher_uses_ai_morph_placeholder():
    """Test that 'ai_morph' transition uses the AIMorphStrategy."""
    stitcher = VideoStitcher()
    files = ["/tmp/1.png", "/tmp/2.png"]
    
    with patch("scripts.video_utils.AIMorphStrategy") as MockStrategy, \
         patch("subprocess.run") as mock_run:
        strategy_instance = MockStrategy.return_value
        strategy_instance.build_command.return_value = ["ffmpeg", "dummy_morph"]
        
        stitcher.stitch(files, "story", transition="ai_morph")
        
        MockStrategy.assert_called()
        mock_run.assert_called_with(["ffmpeg", "dummy_morph"], check=True, capture_output=True)

def test_crossfade_strategy_logic():
    """Test the logic of constructing the ffmpeg command for crossfades."""
    from scripts.video_utils import CrossFadeStrategy
    import os
    
    strategy = CrossFadeStrategy("/tmp")
    files = ["1.png", "2.png", "3.png"]
    duration = 3.0 # Fade duration will be 1.0, offset 2.0
    
    # Mock os.path.isabs/abspath/exists to avoid real filesystem access --
    # _resolve_path() checks os.path.exists() and raises FileNotFoundError
    # otherwise (a real, deliberate safety check, not something to work around
    # by touching real files in a unit test).
    with patch("os.path.isabs", return_value=True), \
         patch("os.path.abspath", side_effect=lambda x: x), \
         patch("os.path.exists", return_value=True):

        cmd = strategy.build_command(files, "/out.mp4", duration)
        
        # Check inputs
        assert "-loop" in cmd
        assert "-t" in cmd
        assert "3.0" in cmd
        assert "1.png" in cmd
        
        # Check filter complex
        filter_idx = cmd.index("-filter_complex")
        filter_complex = cmd[filter_idx + 1]
        
        # Expected:
        # [0][1]xfade=transition=fade:duration=1.0:offset=2.0[v0];
        # [v0][2]xfade=transition=fade:duration=1.0:offset=4.0[v1]
        
        assert "[0][1]xfade=transition=fade:duration=1.0:offset=2.0[v0]" in filter_complex
        assert "[v0][2]xfade=transition=fade:duration=1.0:offset=4.0[v1]" in filter_complex
        
        # Check map
        map_idx = cmd.index("-map")
        assert cmd[map_idx + 1] == "[v1]"
