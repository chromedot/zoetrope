#!/bin/bash

# Navigate to the project root
cd /data/comfy

# Activate the virtual environment
source comfyui-env/bin/activate

# Set hardware environment variables
export CUDA_VISIBLE_DEVICES=0

# Launch ComfyUI with Native FP8 Optimizations (Best for Blackwell GB10)
cd ComfyUI
python main.py --listen 0.0.0.0 --highvram --reserve-vram 15 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --fast --output-directory /data/comfy/output --user-directory /data/comfy
