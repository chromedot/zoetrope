# Track Plan: Advanced Audio Generation

This plan outlines the steps to implement Sound Effects and Music generation.

## Phase 1: ComfyUI Audio Capability [checkpoint: pending]
Goal: Enable ComfyUI to generate audio from text.

- [x] Task: Install `comfyui-audioldm` (or recommended audio node) into `ComfyUI/custom_nodes`.
- [ ] Task: Download necessary models (AudioLDM2) to `ComfyUI/models/checkpoints` or `audio_checkpoints`.
- [ ] Task: Create and test a basic Audio Generation workflow (`audio_workflow.json`).
- [ ] Task: Conductor - User Manual Verification 'Phase 1: ComfyUI Audio Capability' (Protocol in workflow.md)

## Phase 2: Backend Integration [checkpoint: pending]
Goal: Connect Studio Backend to the new ComfyUI Audio Workflow.

- [x] Task: Update `StoryManager` to handle `audio_prompt` and `background_audio_file` fields. (Implemented as direct endpoint for MVP)
- [x] Task: Create `scripts/generate_audio_sfx.py` or update `StoryManager.generate_scene` logic to handle audio workflows. (Implemented in `scripts/audio_utils.py`)
- [x] Task: Implement `POST /api/generate_sfx` endpoint in `app.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Backend Integration' (Protocol in workflow.md)

## Phase 3: Frontend Interface [checkpoint: completed]
Goal: Allow users to trigger SFX generation from the UI.

- [x] Task: Update `studio/templates/editor.html` to add "Background Audio" section (Prompt input + Generate button).
- [x] Task: Add audio player for the generated background audio.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Frontend Interface' (Protocol in workflow.md)
