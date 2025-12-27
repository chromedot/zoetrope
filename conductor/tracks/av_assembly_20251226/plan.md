# Track Plan: Audio-Visual Assembly

## Phase 1: Enhanced VideoStitcher Logic [checkpoint: pending]
Goal: Update the backend to mix audio and sync with video.

- [x] Task: Update `TransitionStrategy` in `video_utils.py` to accept audio file paths for each image. [8527ae3]
- [x] Task: Implement `AudioMixedStrategy` (or update existing ones) to use `ffmpeg -i image -i narration -i sfx` with `filter_complex`. [ce9d9d4]
- [x] Task: Create a standalone test script `tests-studio/test_av_assembly.py` to verify a 2-scene render. [ce9d9d4]
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Enhanced VideoStitcher'

## Phase 2: Studio API & Data Mapping [checkpoint: pending]
Goal: Map story data (narration/sfx) to the video request.

- [ ] Task: Update `VideoRequest` pydantic model in `app.py` to include optional audio lists.
- [ ] Task: Update `api/generate_video` to fetch narration and sfx paths from the database/manager if not provided.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: API Integration'

## Phase 3: UI Controls [checkpoint: pending]
Goal: Allow users to toggle audio in the final video.

- [ ] Task: Add "Include Audio" and "Include SFX" checkboxes to the Gallery's video generation modal.
- [ ] Task: Final project walkthrough with Adam and Ivan.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Assembly'
