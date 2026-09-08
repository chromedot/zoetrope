import json
import random
import urllib.request
import os
import re
import datetime
import glob

# Generation resolution, per output format.
#
# Both are ~1.03 megapixels and exact transposes of each other, so a vertical
# scene costs the same GPU time as a landscape one (~44s on the GB10), and
# neither strays from the aspect ratios Flux handles well.
#
# These are *generation* sizes, deliberately not delivery sizes. Asking the
# model for a full 1080x1920 (2.07MP) is both slower and more prone to
# composition artifacts than generating at ~1MP and letting ffmpeg scale up
# during assembly -- 768x1344 and 1080x1920 are both exactly 9:16, so that
# scale is a clean resize with no crop and no letterboxing.
RESOLUTIONS = {
    "vertical": (768, 1344),    # 9:16 -- YouTube Shorts, Reels, TikTok
    "landscape": (1344, 768),   # 16:9 -- standard YouTube
}
DEFAULT_ORIENTATION = "vertical"

# LTX-2.5 text-to-video generation, per output format.
#
# Smaller than the still resolutions above because a clip is ~100 frames rather
# than one: at 27x realtime on the GB10, 576x1024 for 4 seconds takes a couple
# of minutes, and going up scales that linearly. ffmpeg scales to delivery size
# at assembly, exactly as it does for stills.
#
# LTX constrains both dimensions to multiples of 32; these are, and they keep
# the same 9:16 and 16:9 ratios as RESOLUTIONS.
LTX_RESOLUTIONS = {
    "vertical": (576, 1024),
    "landscape": (1024, 576),
}
# LTX requires (frames % 8 == 1). 97 frames is 4.0s at 24fps.
LTX_FRAMES = 97
LTX_FPS = 24


class StoryManager:
    def __init__(self, story_file):
        self.story_file = os.path.abspath(story_file)
        
        # Base dir resolution with Env Var override
        if os.environ.get("BASE_DIR"):
            base_dir = os.environ.get("BASE_DIR")
        else:
            # Resolve paths relative to this script's location
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        self.comfy_url = os.environ.get("COMFY_URL", "http://127.0.0.1:8188/prompt")
        self.story_data = self.load_story()
        
        # Determine story name for file paths
        self.story_name = os.path.splitext(os.path.basename(story_file))[0]
        
        # Output dir resolution
        if os.environ.get("OUTPUT_DIR"):
            # If strictly set, use it. Note: might need story_name appended if generic mount.
            # Assuming OUTPUT_DIR points to the root output folder.
            self.output_dir = os.path.join(os.environ.get("OUTPUT_DIR"), self.story_name)
        else:
            self.output_dir = os.path.join(base_dir, 'output', self.story_name)

        # Workflow template resolution
        if os.environ.get("WORKFLOW_TEMPLATE"):
            self.workflow_template = os.environ.get("WORKFLOW_TEMPLATE")
        else:
            self.workflow_template = os.path.join(base_dir, 'data', 'workflows', 'flux_photoreal_api.json')

        # Output orientation. Env var override follows the same convention as
        # BASE_DIR/OUTPUT_DIR/WORKFLOW_TEMPLATE above; an unrecognised value
        # falls back to the default rather than generating at a broken size.
        orientation = os.environ.get("ORIENTATION", DEFAULT_ORIENTATION).lower()
        if orientation not in RESOLUTIONS:
            orientation = DEFAULT_ORIENTATION
        self.orientation = orientation
        self.width, self.height = RESOLUTIONS[orientation]

        with open(self.workflow_template, 'r') as f:
            self.base_workflow = json.load(f)

        # LTX-2.5 video generation. Separate template from the still workflow
        # because it is a different model stack, and optional: a checkout
        # without the LTX weights still runs the image pipeline. Absence is
        # reported when a video is requested, not at startup.
        self.ltx_workflow_template = os.environ.get(
            "LTX_WORKFLOW_TEMPLATE",
            os.path.join(base_dir, 'data', 'workflows', 'ltx25_t2v_api.json'),
        )
        self.ltx_width, self.ltx_height = LTX_RESOLUTIONS[self.orientation]

        self.refresh_image_paths()
        self.refresh_audio_paths()

    def refresh_audio_paths(self):
        """Scans audio directory for existing narration and SFX files."""
        audio_dir = os.path.join(self.output_dir, "audio")
        if not os.path.exists(audio_dir):
            return

        updated = False
        for scene in self.story_data:
            # 1. Narration
            safe_desc = self.sanitize_filename(scene['description'])
            narration_prefix = f"scene_{scene['scene']:02d}_{safe_desc}"
            narration_files = glob.glob(os.path.join(audio_dir, narration_prefix + "*.mp3"))
            
            if narration_files:
                narration_files.sort(key=os.path.getmtime, reverse=True)
                filename = os.path.basename(narration_files[0])
                actual_path = f"{self.story_name}/audio/{filename}"
                if scene.get('audio_file') != actual_path:
                    scene['audio_file'] = actual_path
                    updated = True
            
            # 2. SFX
            sfx_prefix = f"scene_{scene['scene']:02d}_sfx"
            sfx_files = glob.glob(os.path.join(audio_dir, sfx_prefix + "*.flac"))
            
            if sfx_files:
                sfx_files.sort(key=os.path.getmtime, reverse=True)
                filename = os.path.basename(sfx_files[0])
                actual_path = f"{self.story_name}/audio/{filename}"
                if scene.get('sfx_file') != actual_path:
                    scene['sfx_file'] = actual_path
                    updated = True
        
        if updated:
            self.save_story()

    def refresh_image_paths(self):
        """Scans output directory for existing images and updates story data."""
        if not os.path.exists(self.output_dir):
            return

        updated = False
        for scene in self.story_data:
            safe_desc = self.sanitize_filename(scene['description'])
            file_prefix = f"scene_{scene['scene']:02d}_{safe_desc}"
            
            # Search for ANY file containing the scene pattern
            search_pattern = os.path.join(self.output_dir, "*" + file_prefix + "*.png")
            files = glob.glob(search_pattern)
            
            best_file = None
            
            if files:
                # Priority 1: Files starting with "new:"
                new_files = [f for f in files if os.path.basename(f).startswith("new:")]
                if new_files:
                    # If multiple "new" files exist (shouldn't happen), take the newest
                    new_files.sort(key=os.path.getmtime, reverse=True)
                    best_file = new_files[0]
                else:
                    # Priority 2: Just the newest file
                    files.sort(key=os.path.getmtime, reverse=True)
                    best_file = files[0]
            
            if best_file:
                # Store the prefix relative to the output/ folder so TUI logic works.
                # Currently TUI expects "story_name/filename_prefix"
                # But we have complex filenames now.
                # Let's verify what the TUI expects. The TUI does:
                # folder, file_prefix = os.path.split(prefix)
                # glob(folder, file_prefix + "*.png")
                
                # If we store "geronimo/new:14:30_scene_01..."
                # TUI will search for "geronimo/new:14:30_scene_01...*.png"
                # This should work perfectly.
                
                filename = os.path.basename(best_file)
                # Remove the suffix that comfyui adds (_00001_.png) to get the "prefix"
                # But actually, if we include the timestamp in the prefix, we are very specific.
                
                # To be safe, let's store the part before the final counter if possible, 
                # or just the filename without extension.
                prefix_candidate = os.path.splitext(filename)[0]
                
                # Cleanup trailing underscores or counters if we want to be clean, 
                # but exact match is fine too.
                actual_prefix = f"{self.story_name}/{filename}"
                
                if scene.get('image_path') != actual_prefix:
                    scene['image_path'] = actual_prefix
                    updated = True
        
        if updated:
            self.save_story()

    def load_story(self):
        with open(self.story_file, 'r') as f:
            return json.load(f)

    def save_story(self):
        with open(self.story_file, 'w') as f:
            json.dump(self.story_data, f, indent=2)

    def sanitize_filename(self, text):
        return re.sub(r'[^a-zA-Z0-9]', '', text.replace(' ', '_'))

    def generate_scene_video(self, scene_index, seed_mode='random', length=None):
        """
        Submits an LTX-2.5 text-to-video job for the scene at scene_index.

        Returns (seed, prompt_id, prefix). Submission is non-blocking: a clip
        takes minutes, so the caller polls ComfyUI's /history for prompt_id
        rather than waiting here.

        The prefix places the clip under <story>/videos/, which is where the
        video gallery looks for it.
        """
        if not os.path.exists(self.ltx_workflow_template):
            raise Exception(
                f"LTX workflow template not found at {self.ltx_workflow_template}. "
                "Run scripts/download_ltx25.sh to install the LTX-2.5 models."
            )

        scene_data = self.story_data[scene_index]
        with open(self.ltx_workflow_template, 'r') as f:
            workflow = json.load(f)

        frames = length if length is not None else LTX_FRAMES
        if frames % 8 != 1:
            raise ValueError(f"LTX requires frames % 8 == 1; got {frames}")

        current_seed = scene_data.get('seed', 0)
        if seed_mode == 'fixed':
            seed = current_seed if current_seed else random.randint(1, 1000000000000)
        elif seed_mode == 'increment':
            seed = current_seed + 1 if current_seed else random.randint(1, 1000000000000)
        else:
            seed = random.randint(1, 1000000000000)

        timestamp = datetime.datetime.now().strftime("%H%M")
        safe_desc = self.sanitize_filename(scene_data['description'])
        prefix = f"{self.story_name}/videos/ltx_{timestamp}_scene_{scene_data['scene']:02d}_{safe_desc}"

        # Node ids come from data/workflows/ltx25_t2v_api.json.
        workflow["5"]["inputs"]["text"] = scene_data['prompt']
        workflow["8"]["inputs"].update(
            width=self.ltx_width, height=self.ltx_height, length=frames
        )
        workflow["9"]["inputs"]["frames_number"] = frames
        workflow["12"]["inputs"]["noise_seed"] = seed
        workflow["20"]["inputs"]["filename_prefix"] = prefix

        data = json.dumps({"prompt": workflow}).encode('utf-8')
        req = urllib.request.Request(self.comfy_url, data=data)
        try:
            response = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"ComfyUI HTTP Error {e.code}: {error_body}")
            raise Exception(f"ComfyUI Error {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"ComfyUI Error: {e}")

        return seed, response.get("prompt_id"), prefix

    def generate_scene(self, scene_index, seed_mode='random'):
        """
        Generates the scene at scene_index.
        Returns the (seed, image_path) used/generated.
        """
        scene_data = self.story_data[scene_index]
        
        # 0. Archive old "new" files for this scene
        if os.path.exists(self.output_dir):
            safe_desc = self.sanitize_filename(scene_data['description'])
            scene_identifier = f"_scene_{scene_data['scene']:02d}_" # Robust identifier
            
            # Find all files for this scene
            search_pattern = os.path.join(self.output_dir, "*.png")
            all_files = glob.glob(search_pattern)
            
            for file_path in all_files:
                filename = os.path.basename(file_path)
                if scene_identifier in filename and filename.startswith("new:"):
                    # Rename: remove "new:"
                    new_filename = filename.replace("new:", "", 1)
                    print(f"Archiving: {filename} -> {new_filename}")
                    os.rename(file_path, os.path.join(self.output_dir, new_filename))

        # Deep copy template
        workflow = json.loads(json.dumps(self.base_workflow))

        # 1. Setup Prompt
        positive_prompt = f"{scene_data['prompt']} Hyper-realistic, 8k resolution, cinematic lighting, shot on 35mm film."
        workflow["6"]["inputs"]["text"] = positive_prompt

        # 2. Setup Resolution (see RESOLUTIONS at module level)
        if "27" in workflow and "inputs" in workflow["27"]:
            workflow["27"]["inputs"]["width"] = self.width
            workflow["27"]["inputs"]["height"] = self.height
            workflow["27"]["inputs"]["batch_size"] = 1
        if "25" in workflow and "inputs" in workflow["25"]:
            workflow["25"]["inputs"]["width"] = self.width
            workflow["25"]["inputs"]["height"] = self.height

        # 3. Handle Seed based on seed_mode
        current_seed = scene_data.get('seed', 0)
        seed = 0
        
        if seed_mode == 'fixed':
            seed = current_seed if current_seed else random.randint(1, 1000000000000)
        elif seed_mode == 'increment':
            seed = current_seed + 1 if current_seed else random.randint(1, 1000000000000)
        else: # random
            seed = random.randint(1, 1000000000000)
            
        scene_data['seed'] = seed
        
        # Apply Seed
        for key, value in workflow.items():
            if "inputs" in value:
                if "noise_seed" in value["inputs"]:
                    workflow[key]["inputs"]["noise_seed"] = seed
                    break
                if "seed" in value["inputs"]:
                    workflow[key]["inputs"]["seed"] = seed
                    break

        # 4. Handle Filename with "new:" + Timestamp
        timestamp = datetime.datetime.now().strftime("%H%M")
        safe_desc = self.sanitize_filename(scene_data['description'])
        
        # Prefix format: new:HHMM_scene_XX_desc
        # Note: ComfyUI will append _00001_.png
        prefix = f"{self.story_name}/new:{timestamp}_scene_{scene_data['scene']:02d}_{safe_desc}"
        
        # Find SaveImage node
        for key, value in workflow.items():
            if value.get("class_type") == "SaveImage":
                workflow[key]["inputs"]["filename_prefix"] = prefix
                break
        
        # 5. Submit
        p = {"prompt": workflow}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(self.comfy_url, data=data)
        try:
            urllib.request.urlopen(req)
        except urllib.error.HTTPError as e:
            # Capture the full error message from ComfyUI
            error_body = e.read().decode('utf-8')
            print(f"ComfyUI HTTP Error {e.code}: {error_body}")
            raise Exception(f"ComfyUI Error {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"ComfyUI Error: {e}")

        # Update and save
        # We store the prefix. The refresh_image_paths logic handles finding the actual file later.
        # But for immediate feedback, we store this.
        scene_data['image_path'] = prefix 
        self.save_story()
        
        return seed, prefix
