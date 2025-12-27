import os
import shutil
import subprocess
from scripts.video_utils import VideoStitcher

def reproduce():
    output_dir = "temp_reproduce"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Create dummy image
    img = os.path.join(output_dir, "test.png")
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=100x100:d=0.1", "-frames:v", "1", img], check=True, stderr=subprocess.DEVNULL)
    
    stitcher = VideoStitcher(output_root=output_dir)
    
    print("Testing stitch with audio_mixed and empty audio lists...")
    try:
        # Mimic what happens when user unchecks boxes: audio_files=[], sfx_files=[]
        # Pass relative path 'test.png' because stitcher joins with output_root
        stitcher.stitch(
            files=["test.png"],
            story_name="test_story",
            transition="audio_mixed",
            duration=2.0,
            audio_files=[],
            sfx_files=[]
        )
        print("Success!")
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()
