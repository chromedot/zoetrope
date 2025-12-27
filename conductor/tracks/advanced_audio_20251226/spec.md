# Track Spec: Advanced Audio Generation

## Goal
Enable the Story Studio to generate non-speech audio (Sound Effects, Background Music) based on text prompts.

## Core Features
1.  **Audio Prompting:** Users can input a descriptive prompt (e.g., "footsteps on concrete", "epic orchestral music").
2.  **ComfyUI Integration:** Leverage ComfyUI with custom nodes (likely `ComfyUI-AudioLDM` or `ComfyUI-Audio`) to perform the generation.
3.  **Frontend Controls:** A new UI section in the Scene Editor for "Soundscape" or "Background Audio".
4.  **Storage:** Save generated audio files in `output/<story>/audio/` distinct from narration (or alongside it).

## Tech Stack
- **Backend:** Python (FastAPI), interacting with ComfyUI API.
- **AI Model:** AudioLDM2 or MusicGen (via ComfyUI custom nodes).
- **Frontend:** HTML/JS updates to `editor.html`.

## Constraints
- Must run locally.
- Must not break existing Image or TTS workflows.
