import sys
import os
import glob
import json
import asyncio
import time
import datetime
import shutil
import subprocess
import uuid
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import urllib.request

# Add project root to path to allow imports from scripts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.story_manager import StoryManager
from scripts.video_utils import VideoStitcher
from scripts.audio_utils import EdgeTTSGenerator, ComfyAudioGenerator
import database

app = FastAPI()

# Mount static files (css, js, images)
# We need to serve the output directory as static to show images
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/images", StaticFiles(directory=OUTPUT_DIR), name="images")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

# Initialize DB
database.init_db()

# Initialize Manager (default to geronimo.story)
STORY_PATH = os.path.join(BASE_DIR, "data", "stories", "geronimo.story")
manager = StoryManager(STORY_PATH)
stitcher = VideoStitcher(output_root=OUTPUT_DIR)
tts_generator = EdgeTTSGenerator()
sfx_generator = ComfyAudioGenerator()

# ...

def safe_join(base_dir, *paths):
    """
    Safely joins paths and ensures the result is within the base_dir.
    Prevents path traversal attacks.
    """
    try:
        # Join the paths
        final_path = os.path.join(base_dir, *paths)
        # Resolve absolute paths to handle .. and symlinks
        resolved_path = os.path.abspath(final_path)
        resolved_base = os.path.abspath(base_dir)
        
        # Check if the resolved path starts with the resolved base directory
        if not resolved_path.startswith(resolved_base):
            raise ValueError(f"Path traversal attempt: {final_path} is outside {base_dir}")
            
        return resolved_path
    except Exception as e:
        # Log the security event
        print(f"Security Warning: {e}")
        raise ValueError("Invalid path")

class VideoRequest(BaseModel):
    story_name: str
    files: List[str]
    transition: str = "none"
    duration: float = 2.0

class AudioRequest(BaseModel):
    scene_index: int
    text: str
    story_name: str
    voice: str = None

class SFXRequest(BaseModel):
    text: str
    story_name: str

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/gallery")

# ... (rest of endpoints)

@app.post("/api/generate_sfx")
async def generate_sfx(request: SFXRequest):
    try:
        # Output path: output/<story>/audio/sfx_<uuid>.flac
        filename = f"sfx_{uuid.uuid4()}.flac"
        
        # Use safe_join to ensure we are within OUTPUT_DIR
        try:
            story_dir = safe_join(OUTPUT_DIR, request.story_name)
            audio_dir = safe_join(story_dir, "audio")
        except ValueError:
             return {"status": "error", "message": "Invalid story name"}

        os.makedirs(audio_dir, exist_ok=True)
        output_path = os.path.join(audio_dir, filename)
        
        # Generate
        await sfx_generator.generate(request.text, output_path)
        
        # Construct relative path safely
        safe_story_name = os.path.basename(request.story_name) 
        relative_path = f"{safe_story_name}/audio/{filename}"
        
        return {
            "status": "success", 
            "audio_url": f"/images/{relative_path}",
            "filename": filename
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    manager.refresh_image_paths() # Ensure we have latest
    scenes = enrich_scenes_with_ids(manager.story_data)
    return templates.TemplateResponse("gallery.html", {"request": request, "scenes": scenes})

@app.get("/videos", response_class=HTMLResponse)
async def video_gallery(request: Request):
    videos = database.get_all_videos()
    return templates.TemplateResponse("videos.html", {"request": request, "videos": videos})

@app.get("/slideshow", response_class=HTMLResponse)
async def slideshow(request: Request):
    manager.refresh_image_paths()
    return templates.TemplateResponse("slideshow.html", {"request": request, "scenes": manager.story_data})

@app.get("/scene/{scene_index}", response_class=HTMLResponse)
async def editor(request: Request, scene_index: int):
    manager.refresh_image_paths()
    if scene_index < 0 or scene_index >= len(manager.story_data):
        return RedirectResponse(url="/gallery")
    
    # Refresh IDs
    scenes = enrich_scenes_with_ids(manager.story_data)
    scene = scenes[scene_index]
    
    return templates.TemplateResponse("editor.html", {
        "request": request, 
        "scene": scene, 
        "index": scene_index,
        "total": len(manager.story_data)
    })

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    return templates.TemplateResponse("status.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    stories = database.get_dashboard_stats()
    return templates.TemplateResponse("dashboard.html", {"request": request, "stories": stories})

@app.post("/api/update_prompt/{scene_index}")
async def update_prompt(scene_index: int, prompt: str = Form(...)):
    scene = manager.story_data[scene_index]
    scene['prompt'] = prompt
    manager.save_story()
    return {"status": "success", "prompt": prompt}

@app.post("/api/regenerate/{scene_index}")
async def regenerate(scene_index: int, seed_mode: str = 'random'):
    try:
        # We run this synchronously for now as manager isn't async
        seed, prefix = manager.generate_scene(scene_index, seed_mode=seed_mode)
        
        scene = manager.story_data[scene_index]
        
        # Sprint 2: Create robust DB record
        estimated_filename = os.path.basename(prefix) + "_00001_.png"
        run_id = database.create_generation_record(
            scene_index=scene['scene'],
            story_name=manager.story_name,
            prompt=scene['prompt'],
            seed=seed,
            filename=estimated_filename
        )
        
        # Legacy logging (optional, can keep or remove, keeping for safety)
        database.log_generation(scene['scene'], prefix, scene['prompt'], seed)
        
        return {
            "status": "submitted", 
            "seed": seed, 
            "prefix": prefix,
            "run_id": run_id, # Frontend uses this for tracking
            "image_path": prefix
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/check_status")
async def check_status(prefix: str, run_id: int = None):
    """Checks if the image file for the given prefix exists."""
    
    folder, file_prefix = os.path.split(prefix)
    
    try:
        # Verify the folder is safe
        # We treat OUTPUT_DIR as the root
        safe_folder = safe_join(OUTPUT_DIR, folder)
    except ValueError:
        return {"ready": False}
        
    search_path = os.path.join(safe_folder, file_prefix + "*.png")
    files = glob.glob(search_path)
    
    if files:
        # Sort by modification time to get the latest
        latest_file = max(files, key=os.path.getmtime)
        
        # Return relative path for URL
        filename = os.path.basename(latest_file)
        url = f"/images/{folder}/{filename}"
        
        # Sprint 2: Update DB if run_id provided
        if run_id:
            # We need start time to calc duration. 
            # Ideally we'd fetch created_at from DB, but for simplicity:
            # We'll just assume start time was when record was created.
            # Let's get the record to be precise if we want, or just update.
            # We'll calculate duration based on file mtime vs current time? 
            # Or better: current time - created_at.
            # Let's just pass a duration calculation if we can. 
            # For now, I'll calculate duration as (Now - File Modification Time)?? No.
            # I'll just use (Now - Created_At). I need to fetch Created_At.
            # Simplified: Let the DB update handle the timestamp logic or just pass a rough duration.
            # I'll modify update_generation_record to just take the current time and we can calc diff later,
            # or I'll just pass 0 for now if I don't want to query first.
            # Wait, the prompt asked for "average time to make one".
            # I should do: 
            conn = database.get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT created_at FROM generated_images WHERE id=?", (run_id,))
            row = cur.fetchone()
            conn.close()
            
            duration = 0
            if row:
                created_at = datetime.datetime.fromisoformat(row['created_at'])
                duration = (datetime.datetime.now() - created_at).total_seconds()
            
            database.update_generation_record(run_id, filename, duration)
            
            # Fetch the updated ID (it's run_id) to return to frontend?
            # Frontend already has run_id.
            
        return {"ready": True, "url": url, "id": run_id}
    
    return {"ready": False}

@app.get("/api/stats")
async def get_stats():
    return database.get_generation_stats()

@app.get("/api/dashboard")
async def get_dashboard():
    return database.get_dashboard_stats()

@app.post("/api/generate_audio")
async def generate_audio(request: AudioRequest):
    try:
        # Get scene data to get description for filename
        if request.scene_index < 0 or request.scene_index >= len(manager.story_data):
            return {"status": "error", "message": "Invalid scene index"}
            
        scene = manager.story_data[request.scene_index]
        # Use UUID for collision-proof filename
        # Format: scene_<index>_<uuid>.mp3
        filename = f"scene_{scene['scene']:02d}_{uuid.uuid4()}.mp3"
        
        try:
            story_dir = safe_join(OUTPUT_DIR, request.story_name)
            audio_dir = safe_join(story_dir, "audio")
        except ValueError:
            return {"status": "error", "message": "Invalid story name"}

        os.makedirs(audio_dir, exist_ok=True)
        output_path = os.path.join(audio_dir, filename)
        
        # Generate Audio
        await tts_generator.generate(request.text, output_path, voice=request.voice)
        
        # Update Story Data
        safe_story_name = os.path.basename(request.story_name)
        relative_path = f"{safe_story_name}/audio/{filename}"
        scene['narration_text'] = request.text
        scene['audio_file'] = relative_path
        manager.save_story()
        
        # Update Database
        database.update_scene_narration(request.story_name, scene['scene'], request.text, relative_path)
        
        return {
            "status": "success", 
            "audio_url": f"/images/{relative_path}",
            "filename": filename
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate_video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    video_id = database.create_video_record(
        story_name=request.story_name,
        transition=request.transition,
        duration=request.duration
    )
    
    background_tasks.add_task(
        perform_stitching,
        video_id=video_id,
        files=request.files,
        story_name=request.story_name,
        transition=request.transition,
        duration=request.duration
    )
    
    return {"status": "submitted", "video_id": video_id}

@app.post("/api/delete_story/{story_name}")
async def delete_story(story_name: str):
    database.delete_story_generations(story_name)
    return {"status": "success"}

@app.post("/api/delete_video/{video_id}")
async def delete_video(video_id: int):
    database.delete_video_record(video_id)
    return {"status": "success"}

@app.get("/api/queue")
async def get_queue():
    try:
        # Fetch from ComfyUI
        with urllib.request.urlopen("http://127.0.0.1:8188/queue") as response:
            data = json.loads(response.read().decode())
            # Data format: {"queue_running": [...], "queue_pending": [...]}
            running = len(data.get("queue_running", []))
            pending = len(data.get("queue_pending", []))
            return {"status": "success", "running": running, "pending": pending}
    except Exception as e:
        return {"status": "error", "running": 0, "pending": 0, "message": str(e)}

@app.get("/api/system_stats")
async def get_system_stats():
    stats = {
        "cpu_usage": 0,
        "ram_usage": 0,
        "gpu_usage": 0,
        "gpu_temp": 0,
        "fan_speed": 0
    }
    
    # CPU / RAM
    try:
        # Load average (1 min)
        load1, _, _ = os.getloadavg()
        stats["cpu_usage"] = round(load1 / os.cpu_count() * 100, 1) # Rough estimate
        
        # RAM
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.readlines()
        mem_total = int(meminfo[0].split()[1])
        mem_available = int(meminfo[2].split()[1])
        stats["ram_usage"] = round((mem_total - mem_available) / mem_total * 100, 1)
    except:
        pass
        
    # GPU (nvidia-smi)
    try:
        # Run nvidia-smi to get utilization and temp
        # format: utilization.gpu, temperature.gpu, fan.speed
        cmd = "nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,fan.speed --format=csv,noheader,nounits"
        result = subprocess.check_output(cmd.split()).decode().strip()
        parts = result.split(',')
        if len(parts) >= 3:
            stats["gpu_usage"] = int(parts[0].strip())
            stats["gpu_temp"] = int(parts[1].strip())
            stats["fan_speed"] = int(parts[2].strip())
    except:
        # GPU stats might fail if not nvidia or container restricted
        pass
        
    return stats

@app.post("/api/refine_prompt")
async def refine_prompt(prompt: str = Form(...), instructions: str = Form(...)):
    """
    Mock AI refinement for now, or use google-generativeai if installed.
    """
    try:
        import google.generativeai as genai
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return {"status": "error", "message": "GEMINI_API_KEY not set on server."}
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        full_prompt = f"Original Image Prompt: {prompt}\n\nUser Instructions: {instructions}\n\nRewrite the prompt to incorporate the instructions while maintaining high quality style keywords."
        
        response = model.generate_content(full_prompt)
        return {"status": "success", "new_prompt": response.text}
        
    except ImportError:
        return {"status": "error", "message": "google-generativeai library not installed."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def enrich_scenes_with_ids(scenes):
    enriched = []
    for scene in scenes:
        s = scene.copy()
        if s.get('image_path'):
            try:
                db_id = database.get_image_id_by_filename(s['image_path'])
                s['db_id'] = db_id
            except Exception:
                s['db_id'] = None
        else:
            s['db_id'] = None
        enriched.append(s)
    return enriched

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8189)
