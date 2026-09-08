import os
import subprocess
import datetime
import logging
from abc import ABC, abstractmethod
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

logger = logging.getLogger(__name__)

class TransitionStrategy(ABC):
    def __init__(self, output_root):
        self.output_root = output_root

    def _resolve_path(self, file_path):
        if not os.path.isabs(file_path):
            full_path = os.path.abspath(os.path.join(self.output_root, file_path))
        else:
            full_path = file_path
        
        if not os.path.exists(full_path):
            # Log warning or raise error? Raising error is safer for ffmpeg.
            logger.error(f"File not found: {full_path}")
            raise FileNotFoundError(f"File not found: {full_path}")
        return full_path

    @abstractmethod
    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
        pass

class SimpleCutStrategy(TransitionStrategy):
    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
        if not files:
            return None

        list_path = output_path + ".txt"
        
        if audio_files or sfx_files:
            logger.warning("SimpleCutStrategy does not support audio mixing yet. Audio files will be ignored.")

        with open(list_path, "w") as f:
            for file_path in files:
                full_path = self._resolve_path(file_path)
                
                f.write(f"file '{full_path}'\n")
                f.write(f"duration {duration}\n")
            
            last_full_path = self._resolve_path(files[-1])
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
    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
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
            full_path = self._resolve_path(f)
            inputs.extend(["-loop", "1", "-t", str(duration), "-i", full_path])
            
        # Build Filter Complex
        # [0][1]xfade=transition=fade:duration=1:offset=2[v0];
        # [v0][2]xfade=transition=fade:duration=1:offset=4[v1];
        filter_complex = ""
        current_offset = offset_step
        
        # Special case: 1 file -> just copy
        if len(files) == 1:
            return SimpleCutStrategy(self.output_root).build_command(files, output_path, duration, audio_files, sfx_files)

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
    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
        logger.warning("AI Morph not implemented. Using fallback.")
        return SimpleCutStrategy(self.output_root).build_command(files, output_path, duration, audio_files, sfx_files)

class AudioMixedStrategy(TransitionStrategy):
    def _get_audio_duration(self, audio_path):
        if not audio_path or not os.path.exists(audio_path):
            return 0.0
        try:
            cmd = [
                "ffprobe", "-v", "error", 
                "-show_entries", "format=duration", 
                "-of", "default=noprint_wrappers=1:nokey=1", 
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (ValueError, subprocess.CalledProcessError):
            logger.warning(f"Could not determine duration for {audio_path}")
            return 0.0

    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
        if not files:
            return None

        # Build inputs and filter complex
        inputs = []
        filter_complex = ""
        
        # We need to track input indices
        # Structure:
        # [Input 0: Img 0]
        # [Input 1: Audio 0 (optional)]
        # [Input 2: SFX 0 (optional)]
        # ...
        
        input_idx = 0
        video_segments = []
        audio_segments = []
        
        for i, img_file in enumerate(files):
            # Determine Scene Duration
            scene_duration = duration # Default
            
            current_audio = None
            current_sfx = None
            
            if audio_files and i < len(audio_files) and audio_files[i]:
                try:
                    current_audio = self._resolve_path(audio_files[i])
                    audio_dur = self._get_audio_duration(current_audio)
                    if audio_dur > 0:
                        scene_duration = audio_dur
                except FileNotFoundError:
                    logger.warning(f"Audio file not found: {audio_files[i]}, skipping sync.")
            
            if sfx_files and i < len(sfx_files) and sfx_files[i]:
                try:
                    current_sfx = self._resolve_path(sfx_files[i])
                except FileNotFoundError:
                    logger.warning(f"SFX file not found: {sfx_files[i]}")

            # --- Inputs ---
            
            # 1. Video Input (Image)
            img_path = self._resolve_path(img_file)
            inputs.extend(["-loop", "1", "-t", str(scene_duration), "-i", img_path])
            v_in_label = f"[{input_idx}:v]"
            curr_v_idx = input_idx
            input_idx += 1
            
            # 2. Audio/SFX Inputs
            if current_audio and current_sfx:
                # Add both and mix
                inputs.extend(["-i", current_audio])
                a_idx = input_idx
                input_idx += 1
                
                inputs.extend(["-i", current_sfx])
                sfx_idx = input_idx
                input_idx += 1
                
                mix_label = f"a_mix_{i}"
                # Use explicit labels for resampled streams to avoid ambiguity
                filter_complex += f"[{a_idx}:a]aresample=44100[a_res_{i}];[{sfx_idx}:a]aresample=44100[sfx_res_{i}];"
                filter_complex += f"[a_res_{i}][sfx_res_{i}]amix=inputs=2:duration=longest[{mix_label}];"
                mixed_audio_label = f"[{mix_label}]"
                
            elif current_audio:
                inputs.extend(["-i", current_audio])
                curr_a_idx = input_idx
                input_idx += 1
                # Even single stream needs resampling for consistency in concat
                filter_complex += f"[{curr_a_idx}:a]aresample=44100[a_res_{i}];"
                mixed_audio_label = f"[a_res_{i}]"
                
            elif current_sfx:
                inputs.extend(["-i", current_sfx])
                curr_sfx_idx = input_idx
                input_idx += 1
                filter_complex += f"[{curr_sfx_idx}:a]aresample=44100[sfx_res_{i}];"
                mixed_audio_label = f"[sfx_res_{i}]"
                # Sync duration to SFX if no narration
                sfx_dur = self._get_audio_duration(current_sfx)
                if sfx_dur > 0:
                    scene_duration = sfx_dur
                    # Update previous image loop duration
                    # inputs list: [... "-loop", "1", "-t", "DURATION", "-i", "PATH"]
                    # If we just added "-i", "SFX_PATH", then:
                    # N-1: SFX_PATH, N-2: -i
                    # N-3: IMG_PATH, N-4: -i, N-5: DURATION, N-6: -t
                    inputs[len(inputs)-5] = str(scene_duration)
            else:
                # Silence
                inputs.extend(["-f", "lavfi", "-t", str(scene_duration), "-i", "anullsrc=r=44100:cl=mono"])
                curr_a_idx = input_idx
                input_idx += 1
                mixed_audio_label = f"[{curr_a_idx}:a]"

            video_segments.append(v_in_label)
            audio_segments.append(mixed_audio_label)

        # --- Concat ---
        # [v0][a0][v1][a1]...concat=n=N:v=1:a=1[v][a]
        
        concat_str = ""
        for v, a in zip(video_segments, audio_segments):
            concat_str += f"{v}{a}"
            
        filter_complex += f"{concat_str}concat=n={len(files)}:v=1:a=1[v_out][a_out]"
        
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[v_out]",
            "-map", "[a_out]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            # Audio codec
            "-c:a", "aac",
            "-b:a", "192k",
            output_path
        ]
        
        return cmd

class VideoStitcher:
    def __init__(self, output_root=str(PROJECT_ROOT / "output")):
        self.output_root = output_root

    def get_output_path(self, story_name):
        """Generates a unique path for the output MP4."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        video_dir = os.path.join(self.output_root, story_name, "videos")
        os.makedirs(video_dir, exist_ok=True)
        return os.path.join(video_dir, f"{story_name}_{timestamp}.mp4")

    def stitch(self, files, story_name, transition="none", duration=2.0, audio_files=None, sfx_files=None):
        """Executes the stitching process using the selected strategy."""
        output_path = self.get_output_path(story_name)
        
        strategies = {
            "none": SimpleCutStrategy,
            "crossfade": CrossFadeStrategy,
            "ai_morph": AIMorphStrategy,
            "audio_mixed": AudioMixedStrategy
        }
        
        strategy_class = strategies.get(transition, SimpleCutStrategy)
        strategy = strategy_class(self.output_root)
        
        cmd = strategy.build_command(files, output_path, duration, audio_files=audio_files, sfx_files=sfx_files)
        
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