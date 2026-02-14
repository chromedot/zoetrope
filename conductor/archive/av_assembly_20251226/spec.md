# Track Spec: Audio-Visual Assembly

## Goal
Transform the "silent slideshow" into a full multimedia experience by synchronizing images with their respective narration and sound effects.

## Core Features
1.  **Audio Mixing:** Combine Narration (TTS) and Background SFX (AudioLDM) for each scene.
2.  **Scene Duration Sync:** Automatically adjust the duration of each image to match the length of its audio track.
3.  **Video Stitching:** Concatenate these audio-visual clips into a single MP4.
4.  **UI Integration:** Update the "Generate Video" button in the Gallery to include audio options.

## Tech Stack
- **FFmpeg:** Using `filter_complex` for audio mixing and `amix`.
- **Python:** Updating `scripts/video_utils.py` and `studio/app.py`.
- **FastAPI:** Enhancing the `VideoRequest` model.

## Constraints
- Must handle cases where audio is missing (fallback to default duration).
- Must ensure audio/video synchronization doesn't drift.
