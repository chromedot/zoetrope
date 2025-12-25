import json
import random
import urllib.request
import time
import os
import re
import sqlite3
import datetime

# Configuration
STORY_FILE = '/data/comfy/stories/geronimo.story'
TEMPLATE_FILE = '/data/comfy/workflows/flux_photoreal_api.json'
COMFY_URL = "http://127.0.0.1:8188/prompt"
DB_PATH = '/data/comfy/data/story_studio.db'

# Get story name from filename (e.g. "geronimo" from "geronimo.story")
story_name = os.path.splitext(os.path.basename(STORY_FILE))[0]

# 1. Load the Story
with open(STORY_FILE, 'r') as f:
    story_scenes = json.load(f)

# 2. Load the Workflow Template
with open(TEMPLATE_FILE, 'r') as f:
    base_workflow = json.load(f)

def sanitize_filename(text):
    # Remove non-alphanumeric chars and replace spaces with underscores
    return re.sub(r'[^a-zA-Z0-9]', '', text.replace(' ', '_'))

def log_to_db(scene_index, prompt, seed, filename):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        now = datetime.datetime.now()
        c.execute(
            '''INSERT INTO generated_images 
               (scene_index, story_name, prompt, seed, status, created_at, completed_at, generation_duration, filename) 
               VALUES (?, ?, ?, ?, 'completed', ?, ?, 23.0, ?)''',
            (scene_index, story_name, prompt, seed, now, now, filename)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"  -> DB Log Error: {e}")

def queue_scene(scene_data):
    # Deep copy the template
    workflow = json.loads(json.dumps(base_workflow))
    
    # Construct Prompts
    positive_prompt = f"{scene_data['prompt']} Hyper-realistic, 8k resolution, cinematic lighting, shot on 35mm film."
    
    print(f"Queueing Scene {scene_data['scene']}: {scene_data['description']}")
    
    # Update Prompt Node (Node 6)
    workflow["6"]["inputs"]["text"] = positive_prompt

    # Force Resolution 1344x768 (16:9) & Batch Size 1
    if "27" in workflow and "inputs" in workflow["27"]:
        workflow["27"]["inputs"]["width"] = 1344
        workflow["27"]["inputs"]["height"] = 768
        workflow["27"]["inputs"]["batch_size"] = 1
    if "25" in workflow and "inputs" in workflow["25"]:
        workflow["25"]["inputs"]["width"] = 1344
        workflow["25"]["inputs"]["height"] = 768
    
    # Update Filename Prefix for Organization
    safe_desc = sanitize_filename(scene_data['description'])
    prefix = f"{story_name}/scene_{scene_data['scene']:02d}_{safe_desc}"
    
    # Find SaveImage node (usually Node 9)
    save_node_found = False
    for key, value in workflow.items():
        if value.get("class_type") == "SaveImage":
            workflow[key]["inputs"]["filename_prefix"] = prefix
            save_node_found = True
            break
            
    if not save_node_found:
        print("Warning: Could not find SaveImage node to update filename.")

    # Randomize Seed
    seed = random.randint(1, 1000000000000)
    for key, value in workflow.items():
        if "inputs" in value:
            if "noise_seed" in value["inputs"]:
                workflow[key]["inputs"]["noise_seed"] = seed
                break
            if "seed" in value["inputs"]:
                workflow[key]["inputs"]["seed"] = seed
                break

    # Submit to API
    p = {"prompt": workflow}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request(COMFY_URL, data=data)
    try:
        urllib.request.urlopen(req)
        print("  -> Submitted successfully.")
        estimated_filename = f"{prefix.split('/')[-1]}_00001_.png"
        log_to_db(scene_data['scene'], positive_prompt, seed, estimated_filename)
        
    except Exception as e:
        print(f"  -> Error submitting: {e}")

# 3. Only queue the first scene
if story_scenes:
    queue_scene(story_scenes[0])