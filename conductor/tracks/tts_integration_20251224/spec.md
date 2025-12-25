# Track Spec: Text-to-Speech Integration

## Overview
Implement a Text-to-Speech (TTS) engine to generate audio narration for individual story scenes. This feature will allow users to define a narration script for each scene and generate a corresponding `.wav` or `.mp3` file.

## User Stories
- As a creator, I want to write a narration script for each scene in my story.
- As a creator, I want to click a button to generate audio for a scene so I can hear the narration.
- As a creator, I want the generated audio to be automatically linked to the scene for future video assembly.

## Functional Requirements
- **Backend TTS Engine:**
    - Integrate a high-quality, local TTS model (suggested: Kokoro-82M or a compatible library like `coqui-tts` or `espeak` as a fallback if heavy models are complex to set up initially).
    - Provide an API endpoint to trigger audio generation: `POST /api/generate_audio`.
- **Data Model:**
    - Update `stories` or `scenes` data structure to include `narration_text` and `audio_file_path`.
- **UI Updates:**
    - Add a text area in the Scene Editor for "Narration Script".
    - Add a "Generate Audio" button and an audio player to preview the result.

## Non-Functional Requirements
- **Performance:** TTS generation should happen in the background to avoid blocking the UI.
- **Storage:** Audio files should be stored in `output/<story_name>/audio/`.

## Acceptance Criteria
- [ ] User can save a narration text for a specific scene.
- [ ] User can trigger audio generation.
- [ ] An audio file is created on disk.
- [ ] The UI displays an audio player for the generated file.
