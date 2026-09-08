#!/bin/bash
# Start the web studio
# Assuming run from scripts dir or similar

COMFY_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$COMFY_ROOT/studio" || exit
echo "Starting Zoetrope on http://0.0.0.0:8189"
echo "Logs are being written to $COMFY_ROOT/logs/studio.log"
export DB_PATH="$COMFY_ROOT/data/story_studio.db"
../comfyui-env/bin/python app.py > "$COMFY_ROOT/logs/studio.log" 2>&1
