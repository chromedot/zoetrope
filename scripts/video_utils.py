import os
import subprocess
import datetime
import logging

logger = logging.getLogger(__name__)

class VideoStitcher:
    def __init__(self, output_root="/data/comfy/output"):
        self.output_root = output_root

    def get_output_path(self, story_name):
        """Generates a unique path for the output MP4."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_dir = os.path.join(self.output_root, story_name, "videos")
        os.makedirs(video_dir, exist_ok=True)
        return os.path.join(video_dir, f"{story_name}_{timestamp}.mp4")

    def _build_ffmpeg_command(self, files, output_path, transition="none", duration=2.0):
        """
        Builds the ffmpeg command. 
        For now, implementing simple concatenation (simple cuts).
        """
        if not files:
            return None

        # Simple concat command for images
        # ffmpeg -framerate 1/2 -i img%03d.png -c:v libx264 -r 30 -pix_fmt yuv420p out.mp4
        # Since files might not be sequential names, we use a complex filter or concat demuxer.
        
        # Method: Concat demuxer (reliable for disparate files)
        # We need a temp file for the list
        list_path = output_path + ".txt"
        with open(list_path, "w") as f:
            for file_path in files:
                # Ensure we have the full path
                if not os.path.isabs(file_path):
                    full_path = os.path.abspath(os.path.join(self.output_root, file_path))
                else:
                    full_path = file_path
                
                f.write(f"file '{full_path}'\n")
                f.write(f"duration {duration}\n")
            # Last file needs to be repeated
            if not os.path.isabs(files[-1]):
                last_full_path = os.path.abspath(os.path.join(self.output_root, files[-1]))
            else:
                last_full_path = files[-1]
            f.write(f"file '{last_full_path}'\n")

        # Command: ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -pix_fmt yuv420p out.mp4
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            output_path
        ]
        
        return cmd

    def stitch(self, files, story_name, transition="none", duration=2.0):
        """Executes the stitching process."""
        output_path = self.get_output_path(story_name)
        cmd = self._build_ffmpeg_command(files, output_path, transition, duration)
        
        if not cmd:
            return None

        try:
            logger.info(f"Running ffmpeg: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)
            # Cleanup list file
            if os.path.exists(output_path + ".txt"):
                os.remove(output_path + ".txt")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr.decode()}")
            if os.path.exists(output_path + ".txt"):
                os.remove(output_path + ".txt")
            raise Exception(f"Video generation failed: {e.stderr.decode()}")
