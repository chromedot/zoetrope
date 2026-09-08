#!/bin/bash
# Download the LTX-2.5 model set into this project's ComfyUI model tree.
#
# LTX-2.5 generates synchronized video and audio in one pass.
#
# The transformer is the NVFP4 build rather than the int8-convrot one ComfyUI's
# official template references. Measured on the GB10, NVFP4 is 8% faster warm
# (44.0s vs 48.0s for a 97-frame 576x1024 clip, distinct seeds, three runs each)
# and 2.6 GB smaller. Blackwell's 5th-gen tensor cores accelerate NVFP4 natively
# and comfy.model_management.supports_nvfp4_compute() returns True here; on a
# card where it returns False, use the int8-convrot build instead.
#
# Requires ComfyUI >= 0.32.0 (the LTXAV model support landed there) and a
# Hugging Face account that has accepted the LTX-2.x Community License at
# https://huggingface.co/Lightricks/LTX-2.5 -- the repo is gated, and an
# unauthenticated fetch returns 401 GatedRepo rather than a useful error.
#
#   hf auth login          # once, before running this
#   ./scripts/download_ltx25.sh
#
# Roughly 37 GB. Re-running is safe: completed files are skipped, partial
# downloads resume.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${LTX_MODELS_DIR:-$PROJECT_ROOT/ComfyUI/models}"
REPO="Lightricks/LTX-2.5"
ENHANCER_REPO="Comfy-Org/gemma-4"

# Prefer the project venv's hf, fall back to whatever is on PATH.
if [ -x "$PROJECT_ROOT/comfyui-env/bin/hf" ]; then
    HF="$PROJECT_ROOT/comfyui-env/bin/hf"
elif command -v hf >/dev/null 2>&1; then
    HF="$(command -v hf)"
else
    echo "ERROR: the 'hf' CLI was not found." >&2
    echo "Install it with: $PROJECT_ROOT/comfyui-env/bin/pip install -U huggingface_hub[cli]" >&2
    exit 1
fi

# `hf auth whoami` exits 0 and prints "Not logged in" when there is no token,
# so the exit code alone is not a usable check -- match the output instead.
WHOAMI="$("$HF" auth whoami 2>&1 | head -1)"
if [ -z "$WHOAMI" ] || [[ "$WHOAMI" == *"Not logged in"* ]]; then
    echo "ERROR: not logged in to Hugging Face." >&2
    echo "  1. Accept the licence at https://huggingface.co/$REPO (the repo is gated)" >&2
    echo "  2. Run: $HF auth login" >&2
    exit 1
fi

# repo | repo-relative path | local subdirectory under MODELS_DIR
#
# The prompt enhancer (gemma4_e2b_it) comes from a different repository and is
# a generative model, not a text encoder: it rewrites a terse prompt into the
# motion-and-camera description LTX responds to. ComfyUI's own template enables
# it by default. It is listed last so a failure there still leaves a working
# generation set.
FILES=(
  "$REPO|diffusion_models/ltx-2.5-22b-distilled-transformer-nvfp4.safetensors|diffusion_models"
  "$REPO|text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors|text_encoders"
  "$REPO|vae/ltx-2.5-video-vae-bf16.safetensors|vae"
  "$REPO|vae/ltx-2.5-audio-vae-bf16.safetensors|vae"
  "$REPO|latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors|latent_upscale_models"
  "$ENHANCER_REPO|text_encoders/gemma4_e2b_it_int8_convrot.safetensors|text_encoders"
)

echo "Repo:   $REPO"
echo "Target: $MODELS_DIR"
echo "User:   $WHOAMI"
echo

for entry in "${FILES[@]}"; do
    IFS='|' read -r repo remote subdir <<< "$entry"
    dest="$MODELS_DIR/$subdir"
    name="$(basename "$remote")"

    mkdir -p "$dest"

    if [ -f "$dest/$name" ]; then
        echo "SKIP  $name (already present)"
        continue
    fi

    echo "GET   $name"
    # --local-dir writes the real file rather than a symlink into the hub
    # cache, so the model tree stays readable without the cache alongside it.
    "$HF" download "$repo" "$remote" --local-dir "$dest" --quiet
    # hf preserves the repo's directory structure under --local-dir; flatten
    # it so the file lands where ComfyUI's folder scan expects it.
    if [ -f "$dest/$remote" ]; then
        mv "$dest/$remote" "$dest/$name"
        rm -rf "${dest:?}/${remote%%/*}"
    fi
done

echo
echo "Done. Files in $MODELS_DIR:"
for entry in "${FILES[@]}"; do
    IFS='|' read -r repo remote subdir <<< "$entry"; name="$(basename "$remote")"
    if [ -f "$MODELS_DIR/$subdir/$name" ]; then
        printf '  %6s  %s/%s\n' "$(du -h "$MODELS_DIR/$subdir/$name" | cut -f1)" "$subdir" "$name"
    else
        printf '  %6s  %s/%s\n' "MISSING" "$subdir" "$name"
    fi
done
echo
echo "Restart ComfyUI to pick them up:  ./evergreen.sh restart"
