import sys
import os
import glob
import json
import asyncio
import time
import datetime
import shutil
import subprocess
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import urllib.request

# Add scripts folder to path to import story_manager
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from story_manager import StoryManager
from video_utils import VideoStitcher
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

def perform_stitching(video_id: int, files: list, story_name: str, transition: str, duration: float):
    """Background task to perform video stitching and update DB."""
    try:
        output_path = stitcher.stitch(files, story_name, transition, duration)
        if output_path:
            filename = os.path.basename(output_path)
            database.update_video_record(video_id, filename, status='completed')
    except Exception as e:
        print(f"Video stitching background task failed: {e}")
        database.update_video_record(video_id, None, status='failed')

def enrich_scenes_with_ids(scenes):
    """Helper to inject DB IDs into scene data for display"""
    for scene in scenes:
        if scene.get('image_path'):
            # image_path is like "geronimo/filename.png"
            # DB stores filename or we match by basename
            scene['db_id'] = database.get_image_id_by_filename(scene['image_path'])
        else:
            scene['db_id'] = None
    return scenes

@app.get("/", response_class=HTMLResponse)
async def root():
    return RedirectResponse(url="/gallery")

@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    manager.refresh_image_paths() # Ensure we have latest
    scenes = enrich_scenes_with_ids(manager.story_data)
    return templates.TemplateResponse("gallery.html", {"request": request, "scenes": scenes})

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
    search_path = os.path.join(OUTPUT_DIR, folder, file_prefix + "*.png")
    files = glob.glob(search_path)
    
    if files:
        latest_file = max(files, key=os.path.getmtime)
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

@app.post("/api/delete_story/{story_name}")
async def delete_story(story_name: str):
    database.delete_story_generations(story_name)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
