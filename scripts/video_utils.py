import os
import subprocess
import datetime
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class TransitionStrategy(ABC):
    def __init__(self, output_root):
        self.output_root = output_root

    @abstractmethod
    def build_command(self, files, output_path, duration, audio_files=None):
        pass

class SimpleCutStrategy(TransitionStrategy):
    def build_command(self, files, output_path, duration, audio_files=None):
        if not files:
            return None

        list_path = output_path + ".txt"
        
        if audio_files:
            logger.warning("SimpleCutStrategy does not support audio mixing yet. Audio files will be ignored.")

        with open(list_path, "w") as f:
            for file_path in files:
                if not os.path.isabs(file_path):
                    full_path = os.path.abspath(os.path.join(self.output_root, file_path))
                else:
                    full_path = file_path
                
                f.write(f"file '{full_path}'\n")
                f.write(f"duration {duration}\n")
            if not os.path.isabs(files[-1]):
                last_full_path = os.path.abspath(os.path.join(self.output_root, files[-1]))
            else:
                last_full_path = files[-1]
            f.write(f"file '{last_full_path}'\n")

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

class CrossFadeStrategy(TransitionStrategy):
    def build_command(self, files, output_path, duration, audio_files=None):
        if not files:
            return None
            
        # Crossfade duration (hardcoded default or logic based)
        # We need the image duration to be significantly longer than the fade
        fade_duration = 1.0
        if duration <= fade_duration:
            fade_duration = duration / 2.0
            
        # Calculate offset
        # Offset is (duration - fade_duration)
        offset_step = duration - fade_duration
        
        # Build Inputs
        # ffmpeg -loop 1 -t 3 -i 1.png -loop 1 -t 3 -i 2.png ...
        inputs = []
        for f in files:
            if not os.path.isabs(f):
                full_path = os.path.abspath(os.path.join(self.output_root, f))
            else:
                full_path = f
            inputs.extend(["-loop", "1", "-t", str(duration), "-i", full_path])
            
        # Build Filter Complex
        # [0][1]xfade=transition=fade:duration=1:offset=2[v0];
        # [v0][2]xfade=transition=fade:duration=1:offset=4[v1];
        filter_complex = ""
        current_offset = offset_step
        
        # Special case: 1 file -> just copy
        if len(files) == 1:
            return SimpleCutStrategy(self.output_root).build_command(files, output_path, duration, audio_files)

        for i in range(len(files) - 1):
            if i == 0:
                input_1 = "[0]"
                input_2 = "[1]"
            else:
                input_1 = f"[v{i-1}]"
                input_2 = f"[{i+1}]"
            
            output_label = f"[v{i}]"
            # Last one usually maps to output, but let's label it v{final}
            
            filter_complex += f"{input_1}{input_2}xfade=transition=fade:duration={fade_duration}:offset={current_offset}{output_label};"
            current_offset += offset_step
            
        # Remove trailing semicolon
        filter_complex = filter_complex.rstrip(";")
        
        # Map final output
        final_output_label = f"[v{len(files)-2}]"

        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", final_output_label,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            output_path
        ]
        
        return cmd

class AIMorphStrategy(TransitionStrategy):
    def build_command(self, files, output_path, duration, audio_files=None):
        logger.warning("AI Morph not implemented. Using fallback.")
        return SimpleCutStrategy(self.output_root).build_command(files, output_path, duration, audio_files)

class VideoStitcher:
    def __init__(self, output_root="/data/comfy/output"):
        self.output_root = output_root

    def get_output_path(self, story_name):
        """Generates a unique path for the output MP4."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_dir = os.path.join(self.output_root, story_name, "videos")
        os.makedirs(video_dir, exist_ok=True)
        return os.path.join(video_dir, f"{story_name}_{timestamp}.mp4")

    def stitch(self, files, story_name, transition="none", duration=2.0, audio_files=None):
        """Executes the stitching process using the selected strategy."""
        output_path = self.get_output_path(story_name)
        
        strategies = {
            "none": SimpleCutStrategy,
            "crossfade": CrossFadeStrategy,
            "ai_morph": AIMorphStrategy
        }
        
        strategy_class = strategies.get(transition, SimpleCutStrategy)
        strategy = strategy_class(self.output_root)
        
        cmd = strategy.build_command(files, output_path, duration, audio_files=audio_files)
        
        if not cmd:
            return None

        try:
            logger.info(f"Running ffmpeg ({transition}): {" ".join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True)
            # Cleanup list file if it exists (SimpleCutStrategy creates it)
            if os.path.exists(output_path + ".txt"):
                os.remove(output_path + ".txt")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg error: {e.stderr.decode()}")
            if os.path.exists(output_path + ".txt"):
                os.remove(output_path + ".txt")
            raise Exception(f"Video generation failed: {e.stderr.decode()}")