#!/bin/bash
# Start the web studio
# Assuming run from scripts dir or similar

cd "$(dirname "$0")/../studio" || exit
echo "Starting Story Studio on http://0.0.0.0:8000"
echo "Logs are being written to /data/comfy/logs/studio.log"
export DB_PATH=/data/comfy/data/story_studio.db
../comfyui-env/bin/python app.py > /data/comfy/logs/studio.log 2>&1
