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

# Delivery resolution for the assembled video. Scenes are generated at ~1MP
# (see scripts/story_manager.py RESOLUTIONS) and scaled here, so the delivered
# file matches what the platform expects regardless of generation size.
DELIVERY_SIZES = {
    (9, 16): (1080, 1920),   # Shorts / Reels / TikTok
    (16, 9): (1920, 1080),   # standard YouTube
}


def _delivery_scale_filter(width, height):
    """ffmpeg filter that fits any source into the matching delivery size.

    scale=...:force_original_aspect_ratio=decrease then pad centres the image
    without cropping it, so a source whose aspect doesn't exactly match the
    target is letterboxed rather than having its edges cut off. setsar=1 keeps
    players from re-stretching the result.
    """
    ratio = (9, 16) if height > width else (16, 9)
    dw, dh = DELIVERY_SIZES[ratio]
    return (
        f"scale={dw}:{dh}:force_original_aspect_ratio=decrease,"
        f"pad={dw}:{dh}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    )


class AudioCrossfadeStrategy(AudioMixedStrategy):
    """Narration/SFX mixing AND crossfade transitions.

    AudioMixedStrategy concatenates hard cuts; CrossFadeStrategy crossfades but
    drops audio entirely. Neither alone is usable for a narrated video, which
    wants both.

    The timing works out cleanly. Each scene's video segment is padded to
    (audio duration + fade), and the xfade chain consumes exactly `fade`
    seconds per transition, so the k-th transition begins at:

        offset_k = sum(d_0..d_k) + (k+1)*fade - (k+1)*fade = sum(d_0..d_k)

    i.e. exactly when scene k's narration ends. The audio track is a plain
    concat with no crossfade, so narration is never faded into itself and no
    words are clipped -- the picture dissolves across the boundary while the
    audio cuts cleanly, which is how a normal edit behaves.
    """

    def build_command(self, files, output_path, duration, audio_files=None, sfx_files=None):
        if not files:
            return None
        if len(files) == 1:
            return AudioMixedStrategy(self.output_root).build_command(
                files, output_path, duration, audio_files, sfx_files
            )

        fade = 1.0
        inputs = []
        filter_complex = ""
        scene_durations = []
        audio_labels = []
        input_idx = 0

        for i, img_file in enumerate(files):
            current_audio = None
            current_sfx = None
            scene_duration = duration

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

            # A scene lasts as long as its longest audio element. Sizing it to
            # the narration alone is not enough: narration and SFX are mixed
            # with amix=duration=longest, so any SFX running past its narration
            # gets truncated. Measured before this was accounted for: 8.07s of
            # SFX lost across a 10-scene story.
            if current_sfx:
                sfx_dur = self._get_audio_duration(current_sfx)
                if sfx_dur > 0:
                    scene_duration = max(scene_duration, sfx_dur) if current_audio else sfx_dur

            scene_durations.append(scene_duration)

            # Video: pad by `fade` so the crossfade overlap doesn't eat into
            # the time this scene is actually on screen.
            img_path = self._resolve_path(img_file)
            inputs.extend(["-loop", "1", "-t", str(scene_duration + fade), "-i", img_path])
            filter_complex += f"[{input_idx}:v]{_delivery_scale_filter(*self._probe_size(img_path))},fps=30,format=yuv420p[v{i}];"
            input_idx += 1

            # Audio: narration and SFX mixed, or silence to hold the slot.
            if current_audio and current_sfx:
                inputs.extend(["-i", current_audio, "-i", current_sfx])
                a_idx, sfx_idx = input_idx, input_idx + 1
                input_idx += 2
                filter_complex += (
                    f"[{a_idx}:a]aresample=44100[ar{i}];"
                    f"[{sfx_idx}:a]aresample=44100[sr{i}];"
                    f"[ar{i}][sr{i}]amix=inputs=2:duration=longest[a{i}];"
                )
            elif current_audio or current_sfx:
                inputs.extend(["-i", current_audio or current_sfx])
                filter_complex += f"[{input_idx}:a]aresample=44100[a{i}];"
                input_idx += 1
            else:
                inputs.extend(["-f", "lavfi", "-t", str(scene_duration), "-i", "anullsrc=r=44100:cl=mono"])
                filter_complex += f"[{input_idx}:a]aresample=44100[a{i}];"
                input_idx += 1
            audio_labels.append(f"[a{i}]")

        # Chain the video crossfades. offset_k lands on the end of scene k's
        # narration, per the docstring.
        cumulative = 0.0
        current_label = "[v0]"
        for i in range(1, len(files)):
            cumulative += scene_durations[i - 1]
            out_label = "[vout]" if i == len(files) - 1 else f"[vx{i}]"
            filter_complex += (
                f"{current_label}[v{i}]xfade=transition=fade:"
                f"duration={fade}:offset={cumulative:.3f}{out_label};"
            )
            current_label = out_label

        filter_complex += "".join(audio_labels) + f"concat=n={len(files)}:v=0:a=1[aout]"

        return [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", "[aout]",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-c:a", "aac",
            "-b:a", "192k",
            # Video runs `fade` longer than the audio (the last segment keeps
            # its pad); end the file when the narration ends.
            "-shortest",
            output_path,
        ]

    def _probe_size(self, path):
        """(width, height) of an image, so the delivery scale picks the right target."""
        try:
            out = subprocess.run(
                ["ffprobe", "-v", "error", "-select_streams", "v:0",
                 "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", path],
                capture_output=True, text=True, check=True,
            ).stdout.strip()
            w, h = out.split("x")[:2]
            return int(w), int(h)
        except (ValueError, subprocess.CalledProcessError, IndexError):
            logger.warning(f"Could not probe size for {path}; assuming vertical.")
            return (768, 1344)


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
            "audio_mixed": AudioMixedStrategy,
            "audio_crossfade": AudioCrossfadeStrategy,
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