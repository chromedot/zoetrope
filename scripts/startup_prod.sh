#!/bin/bash

# Navigate to the project root
COMFY_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMFY_ROOT"

# Use the venv interpreter by absolute path. `source comfyui-env/bin/activate`
# bakes in an absolute VIRTUAL_ENV from venv-creation time, so after the project
# moved it put a nonexistent dir on PATH and bare `python` resolved to nothing.
PYTHON_BIN="$COMFY_ROOT/comfyui-env/bin/python"

# Set hardware environment variables
export CUDA_VISIBLE_DEVICES=0

# Launch ComfyUI from its directory
cd ComfyUI
"$PYTHON_BIN" main.py --listen 0.0.0.0 --highvram --reserve-vram 15 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --fast --output-directory "$COMFY_ROOT/output" --user-directory "$COMFY_ROOT" > "$COMFY_ROOT/logs/comfyui.log" 2>&1
