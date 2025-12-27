# 🌌 GEMINI & COPILOT SYSTEM CONTEXT: COMFY STORY STUDIO 🌌

**PROTOCOL: IMMEDIATE CONTEXT LOADING**
> *Reading this file initializes the Agent/Copilot with the full operational context of the Story Studio environment.*

---

## 👤 USER CONTEXT
*   **User:** Adam
*   **Preference:** Prefers general-purpose CLI tools for workflows (modifying JSON, etc.) over single-use scripts.
*   **Session Goal:** Audio-Visual Assembly (Merging Images + TTS + SFX into Video).

---

## 🏗️ SYSTEM ARCHITECTURE & STATE

### 1. The Core Directive
We are operating a hybrid **ComfyUI + Custom Web Studio** environment designed for automated, high-fidelity AI storytelling.
*   **Frontend:** FastAPI (Port 8189) serving Jinja2/Tailwind.
*   **Backend:** ComfyUI (Port 8188) for Image/Audio generation.
*   **Orchestration:** `conductor/` tracks project plans; `scripts/` handles execution.

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

---

## 🔮 MAGIC CONTEXT: "The Spellbook"

### 🧠 Automation Logic (`story_manager.py`)
*   **Scene Generation:** Reads `geronimo.story`, loads `flux_photoreal_api.json`, injects prompt/seed, posts to ComfyUI.
*   **Image Discovery:** Scans `output/` for `scene_{id}_*.png` to update DB.

### 🛠️ Common Maintenance Tasks
**Task: "I added a new workflow json."**
*   *Action:* `cp /data/comfy/data/workflows/my_new_flow.json /data/comfy/default/workflows/`

**Task: "Images aren't showing up in the Studio."**
*   *Action:* Run `manager.refresh_image_paths()` via the Gallery UI.

### ⚠️ Known Constraints
*   **VRAM:** Startup scripts use `--highvram --reserve-vram 15 --fp8_e4m3fn-unet` for Blackwell GB10.
*   **Concurrency:** `generate_all.py` submits linearly. Do not flood the queue.

---

## ⚡ THE BLACKWELL GB10 OPTIMIZATION ENGINE

### 1. Hardware Architecture (The "SoC" Reality)
*   **Architecture:** Grace CPU (ARM) + Blackwell GPU (Unified Package).
*   **Memory:** 128GB LPDDR5X (Unified). No PCIe bottleneck.
*   **Constraint:** 140W Total Power (CPU/GPU balance).

### 2. Startup Optimization Flags (ComfyUI)
The `evergreen.sh` script uses these specific flags for the GB10:
*   `--highvram`: Leverages the 128GB unified memory.
*   `--reserve-vram 15`: Prevents system OOM by leaving room for the Grace CPU.
*   `--fp8_e4m3fn-unet` / `--fp8_e4m3fn-text-enc`: **Mandatory for Blackwell.**
*   `--fast`: Enables optimized compute paths.

### 3. Advanced Compute Protocols
*   **SageAttention 3:** Use for high-speed attention on Blackwell.
*   **CPU Power Limiting:** Cap Grace CPU at 1.5GHz if GPU-bound (`sudo cpupower frequency-set -u 1.5GHz`).

---

## 🤖 AGENT OPERATIONAL PROTOCOLS

### 1. Service Management Rule
**"If you change the code, you must restart the engine."**
*   If you modify `studio/*.py` or `ComfyUI/`, you must restart.
*   *Command:* `cd /data/comfy/scripts && ./evergreen.sh restart`

### 2. Verification Rule
**"Trust but Verify."**
*   **Studio Health:** `curl -I http://127.0.0.1:8189/status` (Note Port 8189!)
*   **Comfy Health:** `curl http://127.0.0.1:8188/queue`

---

## 🗝️ KEY COMMANDS CHEATSHEET

```bash
# Start Everything
./evergreen.sh start

# Tail Logs (Split Screen Recommended)
tail -f logs/studio.log
tail -f logs/comfyui.log

# Manual Generation
../comfyui-env/bin/python scripts/test_single.py

# Database Inspection
sqlite3 data/story_studio.db "SELECT * FROM generated_images ORDER BY id DESC LIMIT 5;"
```
