import json
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Configuration
STORY_PATH = PROJECT_ROOT / 'stories' / 'geronimo.story'
OUTPUT_DIRECTORY = PROJECT_ROOT / 'output'

def sanitize_filename(text: str) -> str:
    """Converts a description into a filesystem-safe string."""
    return re.sub(r'[^a-zA-Z0-9]', '', text.replace(' ', '_'))

def main():
    # Automatically derive the folder name from the story filename (e.g., 'geronimo')
    story_name = STORY_PATH.stem
    destination_folder = OUTPUT_DIRECTORY / story_name

    print(f"--- Organizing Story: {story_name} ---")

    # 1. Load the Story
    if not STORY_PATH.exists():
        print(f"Error: Story file not found at {STORY_PATH}")
        return

    with STORY_PATH.open('r') as story_file:
        story_scenes: List[Dict[str, Any]] = json.load(story_file)

    # 2. Identify the most recent images generated
    # We grab the number of files that matches the number of scenes in our story
    all_images = list(OUTPUT_DIRECTORY.glob('*.png'))
    all_images.sort(key=lambda x: x.stat().st_mtime)
    
    # Slice the list to get only the most recent ones needed
    recent_images = all_images[-len(story_scenes):]

    # 3. Create Target Directory
    destination_folder.mkdir(parents=True, exist_ok=True)
    print(f"Target Folder: {destination_folder}")

    # 4. Rename and Move
    print(f"Processing {len(recent_images)} images...")

    for index, original_path in enumerate(recent_images):
        scene_data = story_scenes[index]
        sanitized_description = sanitize_filename(scene_data['description'])
        new_filename = f"scene_{scene_data['scene']:02d}_{sanitized_description}.png"
        destination_path = destination_folder / new_filename
        
        print(f"  [{index+1}/{len(recent_images)}] {original_path.name} -> {new_filename}")
        shutil.move(original_path, destination_path)

    print("Done!")

if __name__ == "__main__":
    main()
