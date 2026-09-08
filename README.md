# Zoetrope

This project automates AI storytelling using ComfyUI for image generation and a custom Web Studio for management.

## Directory Structure

| Directory | Purpose |
| :--- | :--- |
| **`ComfyUI/`** | **The Application.** Contains the backend source code (from GitHub) and `main.py`. |
| **`comfyui-env/`** | **The Environment.** Python virtualenv containing PyTorch and dependencies. |
| **`studio/`** | **The Web UI.** FastAPI application (`app.py`), templates, and static files. |
| **`scripts/`** | **Automation & Startup.** Scripts to launch services and run batch jobs. |
| **`data/`** | **Persistent Data.** Stores `stories/`, `workflows/`, and the `story_studio.db` database. **Note:** Workflows here are copied to `default/workflows` for ComfyUI visibility. |
| **`logs/`** | **Logs.** Centralized logs for both ComfyUI (`comfyui.log`) and Studio (`studio.log`). |
| **`output/`** | **Generated Content.** Final images organized by story name. `ComfyUI/output` is a symlink to this folder. |
| **`models/`** | **Models.** Central storage for Checkpoints, Loras, and embeddings. |
| **`docs/`** | **Documentation.** Project notes (`gemini.md`) and setup guides. |

## Quick Start (Local)

**1. Start up Comfyu and Studio app**
Runs on port **8188**.
```bash
cd scripts
./startup_prod.sh
```

**2. Start the Frontend (Zoetrope)**
Runs on port **8189**.
```bash
cd /data/comfy
./evergreen.sh start (stop, status)
```

**3. Automation**
Generate all scenes in a story:
```bash
cd scripts
../comfyui-env/bin/python generate_all_images.py
```

## Logs
All services log to `/data/comfy/logs/`.
- Backend: `tail -f logs/comfyui.log`
- Frontend: `tail -f logs/studio.log`