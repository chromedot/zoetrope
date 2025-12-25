import json
import random
import urllib.request
import os
import re
import datetime
import glob

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

        with open(self.workflow_template, 'r') as f:
            self.base_workflow = json.load(f)
        self.refresh_image_paths()
        self.refresh_audio_paths()

    def refresh_audio_paths(self):
        """Scans audio directory for existing narration files."""
        audio_dir = os.path.join(self.output_dir, "audio")
        if not os.path.exists(audio_dir):
            return

        updated = False
        for scene in self.story_data:
            safe_desc = self.sanitize_filename(scene['description'])
            # Pattern: scene_01_description.mp3
            prefix = f"scene_{scene['scene']:02d}_{safe_desc}"
            search_pattern = os.path.join(audio_dir, prefix + "*")
            files = glob.glob(search_pattern)
            
            if files:
                # Take the newest one
                files.sort(key=os.path.getmtime, reverse=True)
                filename = os.path.basename(files[0])
                actual_path = f"{self.story_name}/audio/{filename}"
                
                if scene.get('audio_file') != actual_path:
                    scene['audio_file'] = actual_path
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

        # 2. Setup Resolution (16:9)
        if "27" in workflow and "inputs" in workflow["27"]:
            workflow["27"]["inputs"]["width"] = 1344
            workflow["27"]["inputs"]["height"] = 768
            workflow["27"]["inputs"]["batch_size"] = 1
        if "25" in workflow and "inputs" in workflow["25"]:
            workflow["25"]["inputs"]["width"] = 1344
            workflow["25"]["inputs"]["height"] = 768

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
