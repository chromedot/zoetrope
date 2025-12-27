# Track Plan: Text-to-Speech Integration

This plan outlines the steps to implement audio narration.

## Phase 1: Backend TTS Engine & Data [checkpoint: eeed7c2]

 [checkpoint: 3a9e6d2]
Goal: Implement the core TTS logic and update the data model to store narration.

- [x] Task: Research and select a local Python TTS library (e.g., `kokoro-onnx` or `edge-tts`) compatible with the environment.
- [x] Task: Create `scripts/audio_utils.py` with an abstract `AudioGenerator` class and a concrete implementation.
- [x] Task: Write Tests for `AudioGenerator` (mocked output).
- [x] Task: Update `StoryManager` to handle `narration_text` and `audio_file` fields in the story JSON/DB.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Backend TTS Engine' (Protocol in workflow.md)

## Phase 2: API and UI Integration [checkpoint: a152d80]
Goal: Expose TTS via API and add controls to the Scene Editor.

- [x] Task: Implement `POST /api/generate_audio` endpoint. a9315c9
- [x] Task: Update Scene Editor UI (`editor.html`) with Narration text area and "Generate Audio" button. a9315c9
- [x] Task: Implement audio playback in the Scene Editor. a9315c9
- [x] Task: Conductor - User Manual Verification 'Phase 2: API and UI Integration' (Protocol in workflow.md) a152d80
