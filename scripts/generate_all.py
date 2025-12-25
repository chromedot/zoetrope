#!/data/comfy/comfyui-env/bin/python
import sys
import time
import os
from story_manager import StoryManager

# Add web folder to path to import database
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../studio"))
import database

def main():
    # Determine story path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_story = os.path.join(base_dir, "data", "stories", "geronimo.story")
    
    story_path = sys.argv[1] if len(sys.argv) > 1 else default_story
    
    if not os.path.exists(story_path):
        # Fallback to current dir
        if os.path.exists("geronimo.story"):
            story_path = "geronimo.story"
        else:
            print(f"Error: Story file not found at {story_path}")
            sys.exit(1)

    print(f"Loading story from: {story_path}")
    manager = StoryManager(story_path)
    
    # Initialize DB
    database.init_db()
    
    print(f"Found {len(manager.story_data)} scenes.")
    
    for i, scene in enumerate(manager.story_data):
        print(f"Generating Scene {scene['scene']}: {scene['description'][:50]}...")
        try:
            seed, prefix = manager.generate_scene(i)
            print(f"  -> Submitted! Seed: {seed} | Prefix: {prefix}")
            
            # Log to DB
            estimated_filename = os.path.basename(prefix) + "_00001_.png"
            database.create_generation_record(
                scene_index=scene['scene'],
                story_name=manager.story_name,
                prompt=scene['prompt'],
                seed=seed,
                filename=estimated_filename
            )
            
        except Exception as e:
            print(f"  -> Error: {e}")
        
        # Small delay to ensure timestamps might differ slightly if fast, 
        # and to not overwhelm the queue instantly (though ComfyUI handles queues fine)
        time.sleep(1)

    print("All scenes queued successfully.")

if __name__ == "__main__":
    main()
