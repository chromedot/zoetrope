# Project Context: ComfyUI Workspace
**User:** Adam

## System Setup
- **Hardware:** NVIDIA DGX Spark / GB10 (Grace Blackwell ARM64)
- **Environment:** ComfyUI Python environment (`comfyui-env` virtualenv)
- **Primary Goal:** Automated AI Storytelling (Image -> Audio -> Video) for YouTube monetization.
- **Deployment Mode:** **Local Execution** (Docker containers have been deprecated/removed).

## Guidelines for Gemini
- **Succinctness:** Provide direct, technical answers. Avoid long conversational filler.
- **Code First:** When troubleshooting, prioritize showing specific file paths and line changes.
- **Token Management:** Do not attempt to read the `models/` or `.venv/` directories (mapped in .geminiignore).
- **Privileges:** User `amorey` has passwordless sudo access (`/etc/sudoers.d/amorey-no-passwd`).
- **Session Closure Protocol:**
    1.  Proactively anticipate updates to `gemini.md` when Adam indicates the session is ending.
    2.  **Prune:** Remove invalidated info.
    3.  **Review:** Check file structure for un-documented artifacts.
    4.  **Closing:** End with "Sleep well Adam".

## Hardware Context: NVIDIA DGX Spark / GB10 (ARM aarch64)
- **Memory:** **128GB Unified Memory** (LPDDR5X). System RAM *is* VRAM.
- **Optimization Strategy (Production Config):**
    - **Native FP8 Math:** Use `--fp8_e4m3fn-unet --fp8_e4m3fn-text-enc`. Aligns perfectly with Blackwell tensor cores and memory bandwidth.
    - **ComfyUI Flags:** `--listen 0.0.0.0 --highvram --reserve-vram 15 --fast --output-directory /data/comfy/output --user-directory /data/comfy`.
    - **Performance:** Flux inference at 1344x768 (16:9) takes **~23 seconds** per image (1.10s/it).
    - **Disk I/O Fix:** `read_ahead_kb = 8192` (Set via root crontab).

## Repository Structure (New)
- `scripts/`: Boot scripts.
    - `startup_prod.sh`: Starts ComfyUI backend locally.
    - `start_studio.sh`: Starts Web UI locally (Port 8000).
    - `generate_all.py`: Batch generation script (logs to SQLite).
- `src/`: Python automation logic (`run_story.py`, `test_single.py`).
- `stories/`: Content manifest files (`geronimo.story`).
- `workflows/`: ComfyUI JSON API/Workflow templates.
- `docs/`: Documentation (`gemini.md`, `comfy-setup.md`).
- `output/`: Generated images (organized into story subfolders).
- `web/`: FastAPI Web Application source.
- `data/`: SQLite database (`story_studio.db`).

## Story Generation (The "Geronimo" Project)
- **Story Manifest:** `stories/geronimo.story`.
- **Automation Engine:** `src/run_story.py`.
    - **Function:** Reads story JSON, injects prompts into `workflows/flux_photoreal_api.json`, and logs to `data/story_studio.db`.
## Current Project Status
- **Image Pipeline:** Complete and optimized (23s/image using Flux FP8).
- **Automation Logic:** `src/run_story.py` successfully orchestrates the Flux API workflow.
- **Next Phase:** 
    - Integrate **Text-to-Speech (TTS)** for narration.
    - Integrate **Image-to-Video (I2V)** (e.g., Stable Video Diffusion or similar) to animate images.
- **Account Switching:** Adam may switch accounts daily. Gemini should always reference this file upon session start to resume context.

## Network & Access
- **Samba Share:** `\\reliant\data` (Mapped to `/data`). Writable by `amorey`.

## Story Studio (Web UI)
- **Location:** `/data/comfy/web` (App logic).
- **Architecture:** 
    - **Frontend/Controller:** FastAPI app (Port 8000) serving Jinja2 templates.
    - **Backend:** ComfyUI (Port 8188) running locally.
    - **Database:** SQLite (`/data/comfy/data/story_studio.db`) for tracking scenes, prompts, and generation stats.
- **Key Features:**
    - **Gallery & Editor:** Visual management of `stories/geronimo.story`.
    - **Prompt Refinement:** Google Gemini integration for prompt enhancement.
    - **Live Generation:** Triggers Flux workflows via ComfyUI API.
- **Startup:** Run `scripts/start_studio.sh`.
- **Status:** Active (Local Process).

## Lessons Learned
- **NVIDIA GB10 (Blackwell) Support:**
    - **Solution:** Always use `nvcr.io/nvidia/pytorch:24.10-py3` or newer for GB10 on ARM64 if using Docker.
    - **ComfyUI Flags:** Must use `--fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --highvram --reserve-vram 15 --fast` for performance.
- **Unified Memory:** on GB10, VRAM is System RAM. `reserve-vram 15` is safe and effective for Flux in this environment.
- **Database Consistency:** Ensure all scripts (`run_story.py`, `generate_all.py`, `app.py`) point to the unified database path: `/data/comfy/data/story_studio.db`.

## Gemini Added Memories
- The user prefers general-purpose CLI tools for editing workflows (like modifying JSON parameters) rather than hard-coded single-use scripts.
- **Flux Prompting:** To fix "underwear bias" in Flux, use explicit anatomical terms in positive prompt and targeted negatives (e.g. "underwear").
- **Photorealism:** Switch style terms from "illustration" to "hyper-realistic photograph, 8k, 35mm film".
