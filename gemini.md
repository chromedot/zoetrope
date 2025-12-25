# 🌌 GEMINI SYSTEM PROMPT ACTIVATION: COMFY STORY STUDIO 🌌

**PROTOCOL: IMMEDIATE CONTEXT LOADING**
> *Reading this file initializes the Agent with the full operational context of the Story Studio environment.*

---

## 🏗️ SYSTEM ARCHITECTURE & STATE

### 1. The Core Directive
We are operating a hybrid **ComfyUI + Custom Web Studio** environment designed for automated, high-fidelity AI storytelling. The system uses local LLMs (via API) to refine prompts and ComfyUI (Flux models) to generate cinematic 16:9 images.

### 2. File System Truths (The "Golden Paths")
*   **Root:** `/data/comfy`
*   **Outputs (Unified):** `/data/comfy/output`
    *   *CRITICAL:* `ComfyUI/output` is a **SYMLINK** to this directory. All tools must write here.
    *   *Structure:* `output/{story_name}/{filename}`
*   **Workflows:**
    *   *Source of Truth:* `/data/comfy/data/workflows/*.json`
    *   *ComfyUI Visibility:* `/data/comfy/default/workflows/*.json` (must mirror Source)
*   **Database:** `/data/comfy/data/story_studio.db` (SQLite)
*   **Scripts:** `/data/comfy/scripts/` (All automation lives here)

### 3. Operational status (As of Dec 21, 2025)
*   **Startup:** Use `./evergreen.sh start` (manages both Studio & ComfyUI PIDs).
*   **Output Fix:** The "Split Brain" output issue is RESOLVED. `ComfyUI/output` -> `../output`.
*   **Workflow Fix:** Workflows must be copied from `data/` to `default/` to be seen in the UI.

---

## 🔮 MAGIC CONTEXT: "The Spellbook"

### 🧠 Automation Logic (`story_manager.py`)
*   **Scene Generation:**
    1.  Reads `geronimo.story` (JSON).
    2.  Loads `flux_photoreal_api.json` (Workflow Template).
    3.  Injects Prompt & Random Seed.
    4.  Submits to `http://127.0.0.1:8188/prompt`.
    5.  Logs "completed" status to DB immediately (optimistic).
*   **Image Discovery:**
    *   Scans `output/geronimo/` for files matching `scene_{id}_*.png`.
    *   Updates `story_data` with the actual path found.

### 🛠️ Common Maintenance Tasks
**Task: "I added a new workflow json."**
*   *Action:* `cp /data/comfy/data/workflows/my_new_flow.json /data/comfy/default/workflows/`

**Task: "Images aren't showing up in the Studio."**
*   *Action:* Check `/data/comfy/output`. Ensure filenames match the pattern `scene_{NN}_description`. Run `manager.refresh_image_paths()` (triggered by visiting the Gallery).

**Task: "Backup everything."**
*   *Action:* `./backup_to_usb.sh` (Note: It performs an RSYNC DELETE. Local is master.)

### ⚠️ Known Constraints
*   **VRAM:** Running on limited VRAM? Startup scripts use `--highvram --reserve-vram 15 --fp8_e4m3fn-unet` to optimize for Blackwell GB10 / Consumer cards.
*   **Concurrency:** `generate_all.py` submits linearly with a 1s sleep. Do not flood the queue.

## ⚡ THE BLACKWELL GB10 OPTIMIZATION ENGINE

### 1. Hardware Architecture (The "SoC" Reality)
*   **Architecture:** Grace CPU (ARM) + Blackwell GPU (Unified Package).
*   **Memory:** 128GB LPDDR5X (Unified). No PCIe bottleneck (NVLink-C2C @ 900 GB/s).
*   **Constraint:** 140W Total Power (CPU/GPU balance).

### 2. Startup Optimization Flags (ComfyUI)
The `startup_prod.sh` and `evergreen.sh` scripts use these specific flags for the GB10:
*   `--highvram`: Leverages the 128GB unified memory.
*   `--reserve-vram 15`: Prevents system OOM by leaving room for the Grace CPU.
*   `--fp8_e4m3fn-unet` / `--fp8_e4m3fn-text-enc`: **Mandatory for Blackwell.** This architecture excels at FP8. Avoid FP16/FP32 for inference.
*   `--fast`: Enables optimized compute paths.

### 3. Advanced Compute Protocols
*   **SageAttention 3:** Use for high-speed attention on Blackwell (targets FP4/FP8).
*   **CPU Power Limiting:** If GPU-bound, cap Grace CPU at 1.5GHz to "gift" more wattage to the GPU:
    ```bash
    sudo cpupower frequency-set -u 1.5GHz
    ```
*   **Texture Theory:** Use `8k` keywords for high-freq noise (pores/fabric) in close-ups, and `None` for atmosphere/film grain in wide shots to optimize how the Blackwell handles high-frequency detail.

### 4. System Tuning
*   **Compilation:** ARMv9-a+sve2 flags are used for local builds of FFmpeg/OpenCV to leverage the Grace CPU's vectorization capabilities.
*   **Headless Operation:** Disabling GNOME saves ~5-10W of the 140W budget for inference.

### 🐳 FUTURE ARCHITECTURE: DOCKER PROTOCOL
*   **Base Image:** `nvcr.io/nvidia/pytorch:24.03-py3-aarch64` (Must be the `aarch64` variant for Grace CPU).
*   **CUDA Requirement:** 12.8+ is recommended for full Blackwell feature support.
*   **Essential Injections:** `sageattention` (Blackwell branch), `tensorrt_llm`, and `huggingface_hub`.
*   **I/O Strategy:** Use asynchronous "Compute-then-Write" to avoid overheating the Southbridge (100W limit) during massive containerized batch jobs.

---

## 🤖 AGENT OPERATIONAL PROTOCOLS

### 1. Service Management Rule
**"If you change the code, you must restart the engine."**
*   If you modify any Python file in `studio/` (FastAPI) or `ComfyUI/` (Backend), you must restart the services to apply changes.
*   *Command:* `cd /data/comfy/scripts && ./evergreen.sh restart`
*   *Note:* `evergreen.sh` handles PID cleanup automatically.

### 2. Verification Rule
**"Trust but Verify."**
*   Never declare a task "Complete" without testing the endpoint.
*   **After restarting Studio:**
    ```bash
    curl -I http://127.0.0.1:8000/status
    ```
    *(Expect HTTP 200 OK)*
*   **After restarting ComfyUI:**
    ```bash
    curl http://127.0.0.1:8188/queue
    ```
    *(Expect JSON response with queue status)*

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

---
*End of Activation Sequence. Agent is now synced.*
