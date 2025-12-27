from studio.app import perform_stitching
import os

# Dummy stitcher mock if needed, but we want to test the real one?
# The real one is initialized in app.py.

# We need to setup database mock or avoid it
import studio.database as database

# Mock database update
def mock_update(*args, **kwargs):
    print(f"DB Update: {args} {kwargs}")

database.update_video_record = mock_update

# Run
output_dir = "/data/comfy/output"
os.makedirs(output_dir, exist_ok=True)
test_file = os.path.join(output_dir, "test.png")

# Create test.png
import subprocess
subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=red:s=100x100:d=0.1", "-frames:v", "1", test_file], stderr=subprocess.DEVNULL)

print("Running perform_stitching with empty audio...")
perform_stitching(
    video_id=1,
    files=["test.png"], # Relative to output_dir
    story_name="test_story",
    transition="audio_mixed",
    duration=2.0,
    audio_files=[],
    sfx_files=[]
)
print("Done.")
