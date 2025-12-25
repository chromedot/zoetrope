import os
import glob
import re

# Configuration
OUTPUT_DIR = "../output/geronimo"
SCENE_COUNT = 10

def main():
    if not os.path.exists(OUTPUT_DIR):
        print(f"Directory {OUTPUT_DIR} not found.")
        return

    print(f"Scanning {OUTPUT_DIR}...")
    
    # Track latest file for each scene
    latest_files = {}

    # Iterate through all PNG files
    for filename in os.listdir(OUTPUT_DIR):
        if not filename.endswith(".png"):
            continue
            
        # Parse scene number from filename (e.g., "23:15_scene_10_SymbolicFinale.png")
        # Regex looks for "_scene_XX_"
        match = re.search(r"_scene_(\d{2})_", filename)
        if match:
            scene_num = int(match.group(1))
            full_path = os.path.join(OUTPUT_DIR, filename)
            mtime = os.path.getmtime(full_path)
            
            if scene_num not in latest_files:
                latest_files[scene_num] = (mtime, filename)
            else:
                if mtime > latest_files[scene_num][0]:
                    latest_files[scene_num] = (mtime, filename)

    # Rename the latest files
    for scene_num in range(1, SCENE_COUNT + 1):
        if scene_num in latest_files:
            timestamp, filename = latest_files[scene_num]
            
            # Check if already starts with new:
            if filename.startswith("new:"):
                print(f"Scene {scene_num}: '{filename}' is already marked new.")
                continue

            new_filename = f"new:{filename}"
            old_path = os.path.join(OUTPUT_DIR, filename)
            new_path = os.path.join(OUTPUT_DIR, new_filename)
            
            print(f"Scene {scene_num}: Renaming '{filename}' -> '{new_filename}'")
            os.rename(old_path, new_path)
        else:
            print(f"Scene {scene_num}: No images found.")

if __name__ == "__main__":
    main()
