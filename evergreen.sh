#!/bin/bash

# Configuration
COMFY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$COMFY_ROOT/logs"
PID_DIR="$COMFY_ROOT/pids"
COMFY_PID_FILE="$PID_DIR/comfyui.pid"
STUDIO_PID_FILE="$PID_DIR/studio.pid"

mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"
mkdir -p "$COMFY_ROOT/user"

start() {
    echo "Starting Services..."

    # 1. Start ComfyUI (Backend)
    if [ -f "$COMFY_PID_FILE" ] && kill -0 $(cat "$COMFY_PID_FILE") 2>/dev/null; then
        echo "ComfyUI is already running (PID $(cat "$COMFY_PID_FILE"))."
        echo "ComfyUI URL: http://reliant:8188"
    else
        echo "Launching ComfyUI..."
        cd "$COMFY_ROOT"
        # Call the venv interpreter by absolute path rather than `source
        # comfyui-env/bin/activate` + bare `python`. The activate script bakes
        # in an absolute VIRTUAL_ENV at venv-creation time (the original install
        # location, long since moved), so activate put a directory that no
        # longer exists on PATH and `python` resolved to nothing -- ComfyUI died
        # instantly with "nohup: failed to run command 'python'". Same class of
        # bug Step 1 fixed in project code, except this one lives inside a
        # generated file we don't own. The path below is derived from
        # COMFY_ROOT, so it follows the project wherever it lives.
        PYTHON_BIN="$COMFY_ROOT/comfyui-env/bin/python"
        export CUDA_VISIBLE_DEVICES=0

        cd ComfyUI
        nohup "$PYTHON_BIN" main.py --listen 0.0.0.0 --highvram --reserve-vram 15 --fp8_e4m3fn-unet --fp8_e4m3fn-text-enc --fast --output-directory "$COMFY_ROOT/output" --user-directory "$COMFY_ROOT/user" > "$LOG_DIR/comfyui.log" 2>&1 &
        
        PID=$!
        echo $PID > "$COMFY_PID_FILE"
        echo "ComfyUI started with PID $PID. Logs: $LOG_DIR/comfyui.log"
        echo "ComfyUI URL: http://reliant:8188"
    fi

    # 2. Start Studio (Frontend)
    if [ -f "$STUDIO_PID_FILE" ] && kill -0 $(cat "$STUDIO_PID_FILE") 2>/dev/null; then
        echo "Studio is already running (PID $(cat "$STUDIO_PID_FILE"))."
        echo "Studio URL: http://reliant:8189/gallery"
    else
        echo "Launching Zoetrope..."
        cd "$COMFY_ROOT/studio"
        
        export DB_PATH="$COMFY_ROOT/data/story_studio.db"
        # Use the venv python via COMFY_ROOT rather than relying on PATH
        
        nohup "$COMFY_ROOT/comfyui-env/bin/python" app.py > "$LOG_DIR/studio.log" 2>&1 &
        
        PID=$!
        echo $PID > "$STUDIO_PID_FILE"
        echo "Studio started with PID $PID. Logs: $LOG_DIR/studio.log"
        echo "Studio URL: http://reliant:8189/gallery"
    fi
}

stop() {
    echo "Stopping Services..."

    # Stop Studio
    if [ -f "$STUDIO_PID_FILE" ]; then
        PID=$(cat "$STUDIO_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping Studio (PID $PID)..."
            kill $PID
            # Wait for it to die?
            sleep 1
        else
            echo "Studio process $PID not found."
        fi
        rm "$STUDIO_PID_FILE"
    else
        echo "No Studio PID file found. Attempting pkill..."
        pkill -f "python app.py" && echo "Killed by pattern."
    fi

    # Stop ComfyUI
    if [ -f "$COMFY_PID_FILE" ]; then
        PID=$(cat "$COMFY_PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping ComfyUI (PID $PID)..."
            kill $PID
            sleep 1
        else
            echo "ComfyUI process $PID not found."
        fi
        rm "$COMFY_PID_FILE"
    else
        echo "No ComfyUI PID file found. Attempting pkill..."
        # Be careful pking main.py if other things run main.py, but likely unique here
        pkill -f "python main.py --listen" && echo "Killed by pattern."
    fi
    
    echo "Services stopped."
}

status() {
    echo "Checking Status..."
    
    # Check ComfyUI
    if [ -f "$COMFY_PID_FILE" ] && kill -0 $(cat "$COMFY_PID_FILE") 2>/dev/null; then
        echo "✅ ComfyUI is RUNNING (PID $(cat "$COMFY_PID_FILE"))"
        echo "   URL: http://reliant:8188"
        echo "   Logs: tail -f $LOG_DIR/comfyui.log"
    else
        echo "❌ ComfyUI is STOPPED"
    fi

    # Check Studio
    if [ -f "$STUDIO_PID_FILE" ] && kill -0 $(cat "$STUDIO_PID_FILE") 2>/dev/null; then
        echo "✅ Studio  is RUNNING (PID $(cat "$STUDIO_PID_FILE"))"
        echo "   URL: http://reliant:8189/gallery"
        echo "   Logs: tail -f $LOG_DIR/studio.log"
    else
        echo "❌ Studio  is STOPPED"
    fi
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 2
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
