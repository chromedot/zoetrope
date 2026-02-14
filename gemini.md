# 🌌 GEMINI & COPILOT SYSTEM CONTEXT: COMFY STORY STUDIO 🌌

**PROTOCOL: IMMEDIATE CONTEXT LOADING**
> *Reading this file initializes the Agent/Copilot with the full operational context of the Story Studio environment.*

## 👤 USER CONTEXT
*   **User:** Adam
*   **Preference:** Prefers general-purpose CLI tools for workflows (modifying JSON, etc.) over single-use scripts
*   **Session Goal:** 

## ⚡ THE BLACKWELL GB10 OPTIMIZATION ENGINE (Reusable for Similar Hardware Projects)

### 1. Hardware Architecture (The "SoC" Reality)
*   **Architecture:** Grace CPU (ARM) + Blackwell GPU (Unified Package).
*   **Memory:** 128GB LPDDR5X (Unified). No PCIe bottleneck.
*   **Constraint:** 140W Total Power (CPU/GPU balance).
*   **The GB10:** is built on the Blackwell architecture, which introduced 5th-generation Tensor Cores. These cores provide native hardware acceleration for the 4-bit floating-point format (NVFP4), which is even more efficient than the FP8.


### 2. Startup Optimization Flags (ComfyUI)
The `evergreen.sh` script uses these specific flags for the GB10:  These optimizations ensure stable, high-throughput operation on the GB10.
*   `--highvram`: Leverages the 128GB unified memory.
*   `--reserve-vram 15`: Prevents system OOM by leaving room for the Grace CPU.
*   `--fp8_e4m3fn-unet` / `--fp8_e4m3fn-text-enc`: **Mandatory for Blackwell.** #enable FP8 Precision
*   `--fast`: Enables optimized compute paths.

### 3. Advanced Compute Protocols
*   **SageAttention 3:** Use for high-speed attention on Blackwell.
*   **CPU Power Limiting:** Cap Grace CPU at 1.5GHz if GPU-bound (`sudo cpupower frequency-set -u 1.5GHz`).

## 🤖 AGENT OPERATIONAL PROTOCOLS (Reusable General Rules)

### 1. Service Management Rule
**"If you change the code, you must restart the engine."**
*   If you modify `studio/*.py` or `ComfyUI/`, you must restart.
*   *Command:* `./evergreen.sh restart`

### 2. Verification Rule
**"Trust but Verify."**
*   **Studio Health:** `curl http://127.0.0.1:8189/status` 
*   **Comfy Health:** `curl http://127.0.0.1:8188/queue`

## 🗝️ KEY COMMANDS CHEATSHEET (Reusable CLI Snippets)

```bash
# Start Everything
[`evergreen.sh`](evergreen.sh ) start

# Tail Logs (Split Screen Recommended)
tail -f [`logs/studio.log`](logs/studio.log )
tail -f [`logs/comfyui.log`](logs/comfyui.log )

# Manual Generation
../comfyui-env/bin/python [`scripts/test_single.py`](scripts/test_single.py )

# Database Inspection
sqlite3 [`data/story_studio.db`](data/story_studio.db ) "SELECT * FROM generated_images ORDER BY id DESC LIMIT 5;"
```

---

## 🏗️ PROJECT-SPECIFIC: COMFY STORY STUDIO (Copy/Modify for New Projects)

### 1. The Core Directive
We are operating a hybrid **ComfyUI + Custom Web Studio** environment designed for automated, high-fidelity AI storytelling.

### 2. File System Truths (The "Golden Paths")
*   **Root:** `/data/comfy`
*   **Outputs (Unified):** `/data/comfy/output/{story_name}/{filename}`
    *   *CRITICAL:* `ComfyUI/output` is a **SYMLINK** to this directory.
*   **Planning (Conductor):** `/data/comfy/conductor/`
    *   *Tracks:* `conductor/tracks.md` (High-level status).
    *   *Current Track:* `conductor/tracks/av_assembly_20251226/`
*   **Workflows:**
    *   *Source:* `/data/comfy/data/workflows/*.json`
    *   *Live:* `/data/comfy/default/workflows/*.json` (Mirror of Source).
*   **Database:** `/data/comfy/data/story_studio.db` (SQLite).
*   **Scripts:** `/data/comfy/scripts/` (Automation & Startup).

### 3. Operational status (As of Dec 27, 2025)
*   **Startup:** Use `./evergreen.sh start` (manages both Studio & ComfyUI PIDs).
*   **Active Track:** Audio-Visual Assembly (Merging assets into MP4).
*   **Completed:** Advanced Audio (SFX), Story Dashboard, Basic Flux Generation.

#### ComfyUI Section (Backend for Image/Audio Generation)
*   **Port:** 8188
*   **Role:** Handles AI generation via workflows (e.g., Flux models).
*   **Integration:** Scripts like `story_manager.py` post to ComfyUI API.
*   **Constraints:** VRAM limits; use GB10 flags for optimization.

#### Studio Section (Frontend Web UI)
*   **Port:** 8189
*   **Tech:** FastAPI serving Jinja2/Tailwind.
*   **Features:** Story Dashboard, Video Assembly UI.
*   **Database:** Manages `generated_images` and `generated_videos` tables.

## 🔮 MAGIC CONTEXT: "The Spellbook" (Project Automation Logic)
*   **Scene Generation:** Reads `geronimo.story`, loads `flux_photoreal_api.json`, injects prompt/seed, posts to ComfyUI.
*   **Image Discovery:** Scans `output/` for `scene_{id}_*.png` to update DB.

## ⚠️ Known Constraints (Project-Specific)
*   **Concurrency:** `generate_all_images.py` submits linearly. Do not flood the queue.
*   **Database Consistency:** Ensure all scripts point to `/data/comfy/data/story_studio.db`.

## Lessons Learned (Project-Specific Insights)
- **NVIDIA GB10 (Blackwell) Support:**
    - **Solution:** Always use `nvcr.io/nvidia/pytorch:24.10-py3` or newer for GB10 on ARM64 if using Docker.
    - **ComfyUI Flags:** Must use `--fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --highvram --reserve-vram 15 --fast` for performance.
- **Unified Memory:** on GB10, VRAM is System RAM. `reserve-vram 15` is safe and effective for Flux in this environment.
- **Database Consistency:** Ensure all scripts (`run_story.py`, `generate_all_images.py`, `app.py`) point to the unified database path: `/data/comfy/data/story_studio.db`.

## Repository Structure (Project Layout)
- `scripts/`: Boot scripts.
    - `startup_prod.sh`: Starts ComfyUI backend locally.
    - `start_studio.sh`: Starts Web UI locally (Port 8000).
    - `generate_all_images.py`: Batch generation script (logs to SQLite).
- `src/`: Python automation logic (`run_story.py`, `test_single.py`).
- `stories/`: Content manifest files (`geronimo.story`).
- `workflows/`: ComfyUI JSON API/Workflow templates.
- `docs/`: Documentation (`gemini.md`, `comfy-setup.md`).
- `output/`: Generated images (organized into story subfolders).
- `web/`: FastAPI Web Application source.
- `data/`: SQLite database (`story_studio.db`).